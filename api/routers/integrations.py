import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.core.config import settings
from api.core.database import get_db
from api.models.tables import Artifact, Project, Scan
from api.schemas import (
    FeaturesOut,
    GitHubPrCommentIn,
    PolishOut,
    ProjectOut,
    ProjectUpdate,
)
from api.services import billing_service
from api.services.github_service import (
    format_pr_comment,
    parse_webhook_repo,
    post_pr_comment,
    verify_webhook_signature,
)
from api.services.ai_pr_comment import enrich_pr_comment_context
from api.services.llm_polish import polish_markdown
from api.services.scan_runner import run_scan
from api.analyzers.discovery import collect_python_files
from api.analyzers.fastapi_scanner import collect_routes
from pathlib import Path
from api.services.watch_service import watch_manager

from api.services.scan_history import previous_openapi

router = APIRouter(tags=["integrations"])


@router.get("/features", response_model=FeaturesOut)
async def feature_flags():
    return FeaturesOut(
        github=bool(settings.github_token),
        ai_polish=bool(settings.ai_api_key),
        ai_suite=bool(settings.ai_api_key),
        watch=True,
        stripe=billing_service.billing_configured(),
    )


@router.patch("/projects/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: int, body: ProjectUpdate, db: AsyncSession = Depends(get_db)
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    if body.watch_enabled is not None:
        project.watch_enabled = body.watch_enabled
        if body.watch_enabled:
            from pathlib import Path

            root = Path(project.root_path).resolve()
            if root.exists():
                from api.services.watch_service import _tree_mtime

                watch_manager._snapshots[project.id] = _tree_mtime(root)
        else:
            watch_manager._snapshots.pop(project.id, None)
    if body.github_repo is not None:
        project.github_repo = body.github_repo.strip()
    if body.slack_webhook is not None:
        project.slack_webhook = body.slack_webhook.strip()
    await db.commit()
    await db.refresh(project)
    return project


@router.get("/projects/{project_id}/watch/events")
async def watch_events(project_id: int, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    queue = watch_manager.subscribe(project_id)

    async def stream():
        try:
            yield f"data: {json.dumps({'type': 'connected', 'watch_enabled': project.watch_enabled})}\n\n"
            while True:
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=25.0)
                    yield f"data: {msg}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            watch_manager.unsubscribe(project_id, queue)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.post("/projects/{project_id}/artifacts/{artifact_id}/polish", response_model=PolishOut)
async def polish_artifact(
    project_id: int, artifact_id: int, db: AsyncSession = Depends(get_db)
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    if not settings.ai_api_key:
        raise HTTPException(
            400,
            "Set SPECWRIGHT_AI_API_KEY to enable AI polish.",
        )
    if project.plan not in ("pro", "enterprise"):
        raise HTTPException(402, "AI polish requires Pro or Enterprise.")

    result = await db.execute(
        select(Artifact)
        .join(Scan)
        .where(Artifact.id == artifact_id, Scan.project_id == project_id)
    )
    art = result.scalar_one_or_none()
    if not art:
        raise HTTPException(404, "Artifact not found")
    if art.kind not in ("api_docs", "django_docs", "readme") and not art.file_path.endswith(
        ".md"
    ):
        raise HTTPException(400, "Only markdown artifacts can be polished")

    try:
        polished = await polish_markdown(art.content, title=art.title)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    except Exception as e:
        raise HTTPException(502, f"AI polish failed: {e}") from e

    art.content = polished
    art.polished = True
    await db.commit()
    return PolishOut(artifact_id=art.id, content=polished, polished=True)


@router.post("/projects/{project_id}/github/pr-comment")
async def github_pr_comment(
    project_id: int,
    body: GitHubPrCommentIn,
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    repo = (body.github_repo or project.github_repo or "").strip()
    if not repo:
        raise HTTPException(400, "Set github_repo on the project or in the request body")

    prev_openapi = await previous_openapi(db, project_id)
    scan = await run_scan(project, db, trigger="github", previous_openapi=prev_openapi)
    await db.commit()
    result = await db.execute(
        select(Scan).where(Scan.id == scan.id).options(selectinload(Scan.artifacts))
    )
    scan = result.scalar_one()
    stats = json.loads(scan.stats or "{}")
    artifact_lines = [f"`{a.file_path}` — {a.title}" for a in scan.artifacts]
    root = Path(project.root_path).resolve()
    routes = collect_routes(collect_python_files(root), root)
    openapi = next((a.content for a in scan.artifacts if a.kind == "openapi"), "")
    extra = await enrich_pr_comment_context(
        db,
        project_id=project_id,
        project_name=project.name,
        plan=project.plan,
        stats=stats,
        routes=routes,
        openapi=openapi,
    )
    comment = format_pr_comment(
        project.name,
        scan.summary,
        artifact_lines,
        pr_diff=stats.get("pr_diff"),
        score=stats.get("score", {}).get("score"),
        coverage_gaps=stats.get("score", {}).get("gaps"),
        breaking_triage=extra["breaking_triage"],
        migration_note=extra["migration_note"],
        reconcile_count=extra["reconcile_count"],
    )

    try:
        posted = await post_pr_comment(repo, body.pr_number, comment)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    except Exception as e:
        raise HTTPException(502, f"GitHub API error: {e}") from e

    return {"posted": True, "comment_id": posted.get("id"), "html_url": posted.get("html_url")}


@router.post("/github/webhook")
async def github_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    body = await request.body()
    sig = request.headers.get("X-Hub-Signature-256")
    if not verify_webhook_signature(body, sig):
        raise HTTPException(401, "Invalid webhook signature")

    payload = json.loads(body)
    event = request.headers.get("X-GitHub-Event", "")
    if event != "pull_request":
        return {"ok": True, "ignored": True}

    repo, pr_number, action = parse_webhook_repo(payload)
    if not repo or not pr_number or action not in ("opened", "synchronize", "reopened"):
        return {"ok": True, "ignored": True}

    result = await db.execute(
        select(Project).where(Project.github_repo == repo).limit(1)
    )
    project = result.scalar_one_or_none()
    if not project:
        return {"ok": True, "ignored": True, "reason": "no_matching_project"}

    prev_openapi = await previous_openapi(db, project.id)
    scan = await run_scan(
        project, db, trigger="github_webhook", previous_openapi=prev_openapi
    )
    await db.commit()
    r2 = await db.execute(
        select(Scan).where(Scan.id == scan.id).options(selectinload(Scan.artifacts))
    )
    scan_loaded = r2.scalar_one()
    stats = json.loads(scan_loaded.stats or "{}")
    lines = [f"`{a.file_path}` — {a.title}" for a in scan_loaded.artifacts]
    root = Path(project.root_path).resolve()
    routes = collect_routes(collect_python_files(root), root)
    openapi = next((a.content for a in scan_loaded.artifacts if a.kind == "openapi"), "")
    extra = await enrich_pr_comment_context(
        db,
        project_id=project.id,
        project_name=project.name,
        plan=project.plan,
        stats=stats,
        routes=routes,
        openapi=openapi,
    )
    comment = format_pr_comment(
        project.name,
        scan_loaded.summary,
        lines,
        pr_diff=stats.get("pr_diff"),
        score=stats.get("score", {}).get("score"),
        coverage_gaps=stats.get("score", {}).get("gaps"),
        breaking_triage=extra["breaking_triage"],
        migration_note=extra["migration_note"],
        reconcile_count=extra["reconcile_count"],
    )
    project.last_score = stats.get("score", {}).get("score", 0)
    await db.commit()

    try:
        posted = await post_pr_comment(repo, pr_number, comment)
    except Exception as e:
        return {"ok": False, "scan_id": scan_loaded.id, "error": str(e)}

    return {"ok": True, "scan_id": scan_loaded.id, "comment_url": posted.get("html_url")}
