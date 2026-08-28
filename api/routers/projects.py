import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.core.config import settings
from api.core.database import get_db
from api.models.tables import Artifact, Project, Scan
from api.schemas import (
    ArtifactOut,
    ContextOut,
    ProjectCreate,
    ProjectCreateOut,
    ProjectFromGitHubIn,
    ProjectOut,
    ScanOut,
    ScanSummaryOut,
    TestGapFixOut,
)
from api.services.autopilot import run_full_autopilot
from api.services.local_repo_resolve import (
    infer_github_repo,
    looks_like_local_path,
    resolve_github_project_root,
)
from api.services.project_bootstrap import bootstrap_project
from api.services.project_slug import ensure_unique_slug
from api.services.scan_history import previous_openapi
from api.services.scan_runner import run_scan
from api.services.test_gap_fill import fix_test_gaps

router = APIRouter(prefix="/projects", tags=["projects"])


def _scan_summary(scan: Scan | None) -> ScanSummaryOut | None:
    if scan is None:
        return None
    artifact_count = len(getattr(scan, "artifacts", None) or [])
    return ScanSummaryOut(
        id=scan.id,
        project_id=scan.project_id,
        status=scan.status,
        summary=scan.summary,
        trigger=scan.trigger or "manual",
        created_at=scan.created_at,
        artifact_count=artifact_count,
    )


def _project_create_out(
    project: Project,
    scan: Scan | None,
    *,
    connected_via: str = "local",
    connected_message: str = "",
) -> ProjectCreateOut:
    return ProjectCreateOut(
        id=project.id,
        name=project.name,
        root_path=project.root_path,
        framework=project.framework,
        watch_enabled=project.watch_enabled,
        github_repo=project.github_repo,
        plan=project.plan,
        public_slug=project.public_slug,
        badge_public=project.badge_public,
        last_score=project.last_score,
        created_at=project.created_at,
        initial_scan=_scan_summary(scan),
        connected_via=connected_via,
        connected_message=connected_message,
    )


@router.post("", response_model=ProjectCreateOut)
async def create_project(body: ProjectCreate, db: AsyncSession = Depends(get_db)):
    root = Path(body.root_path.strip().strip('"')).resolve()
    if not root.is_dir():
        raise HTTPException(400, f"Path not found: {root}")

    github_repo = (body.github_repo or "").strip()
    if not github_repo:
        github_repo = infer_github_repo(root)

    project = Project(
        name=body.name,
        root_path=str(root),
        framework=body.framework,
        github_repo=github_repo,
        plan="pro" if settings.billing_mock_mode else "starter",
    )
    db.add(project)
    await db.flush()
    project.public_slug = await ensure_unique_slug(db)

    try:
        scan = await bootstrap_project(
            db,
            project,
            trigger="connect",
            auto_watch=body.auto_watch,
            auto_scan=body.auto_scan,
        )
        await db.commit()
        await db.refresh(project)
    except FileNotFoundError as e:
        await db.rollback()
        raise HTTPException(400, str(e)) from e
    except Exception as e:
        await db.rollback()
        raise HTTPException(500, f"Project setup failed: {e}") from e

    try:
        msg = f"Scanning your folder at {root}"
        if github_repo:
            msg += f" (linked to {github_repo})"
        return _project_create_out(project, scan, connected_via="local", connected_message=msg)
    except Exception as e:
        raise HTTPException(500, f"Project created but response failed: {e}") from e


@router.post("/from-github", response_model=ProjectCreateOut)
async def create_project_from_github(
    body: ProjectFromGitHubIn, db: AsyncSession = Depends(get_db)
):
    # User pasted a Windows/macOS path into the GitHub URL field — scan folder directly.
    folder = (body.local_path or "").strip()
    if looks_like_local_path(body.github_url) and not folder:
        folder = body.github_url.strip()
    if folder:
        create = ProjectCreate(
            name=body.name or Path(folder).name,
            root_path=folder,
            framework="auto",
            auto_watch=body.auto_watch,
            auto_scan=body.auto_scan,
        )
        return await create_project(create, db)

    try:
        root, owner, repo, source, connect_msg = resolve_github_project_root(
            body.github_url,
            local_path=body.local_path,
            prefer_local=body.prefer_local,
        )
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    except RuntimeError as e:
        raise HTTPException(502, str(e)) from e

    project = Project(
        name=body.name or repo,
        root_path=str(root),
        framework="auto",
        github_repo=f"{owner}/{repo}",
        plan="pro" if settings.billing_mock_mode else "starter",
    )
    db.add(project)
    await db.flush()
    project.public_slug = await ensure_unique_slug(db)

    try:
        scan = await bootstrap_project(
            db,
            project,
            trigger="github_connect",
            auto_watch=body.auto_watch,
            auto_scan=body.auto_scan,
        )
        await db.commit()
        await db.refresh(project)
    except FileNotFoundError as e:
        await db.rollback()
        raise HTTPException(400, str(e)) from e
    except Exception as e:
        await db.rollback()
        raise HTTPException(500, f"GitHub project setup failed: {e}") from e

    return _project_create_out(
        project,
        scan,
        connected_via=source,
        connected_message=connect_msg,
    )


@router.get("", response_model=list[ProjectOut])
async def list_projects(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).order_by(Project.created_at.desc()))
    return result.scalars().all()


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return project


@router.post("/{project_id}/scan", response_model=ScanOut)
async def scan_project(project_id: int, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    try:
        prev = await previous_openapi(db, project_id)
        scan = await run_scan(project, db, previous_openapi=prev)
        stats = json.loads(scan.stats or "{}")
        project.last_score = stats.get("score", {}).get("score", 0)
        await db.commit()
    except FileNotFoundError as e:
        raise HTTPException(400, str(e)) from e
    except Exception as e:
        raise HTTPException(500, f"Scan failed: {e}") from e

    result = await db.execute(
        select(Scan).where(Scan.id == scan.id).options(selectinload(Scan.artifacts))
    )
    return result.scalar_one()


@router.post("/{project_id}/fix-tests", response_model=TestGapFixOut)
async def fix_project_tests(project_id: int, db: AsyncSession = Depends(get_db)):
    """Scaffold tests for every route and AI-enhance gaps — no full rescan required."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    try:
        payload = await fix_test_gaps(project, db)
        await db.commit()
    except LookupError as e:
        raise HTTPException(400, str(e)) from e
    except FileNotFoundError as e:
        raise HTTPException(400, str(e)) from e
    except Exception as e:
        raise HTTPException(500, f"Test gap fix failed: {e}") from e
    return TestGapFixOut(**payload)


@router.post("/{project_id}/autopilot")
async def run_project_autopilot(project_id: int, db: AsyncSession = Depends(get_db)):
    """Full rescan + autopilot: docs, tests, CI sync, score — one shot."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    try:
        payload = await run_full_autopilot(project, db)
        await db.commit()
    except FileNotFoundError as e:
        raise HTTPException(400, str(e)) from e
    except Exception as e:
        raise HTTPException(500, f"Autopilot failed: {e}") from e
    return payload


@router.get("/{project_id}/scans", response_model=list[ScanOut])
async def list_scans(project_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Scan)
        .where(Scan.project_id == project_id)
        .options(selectinload(Scan.artifacts))
        .order_by(Scan.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{project_id}/context", response_model=ContextOut)
async def project_context(project_id: int, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    result = await db.execute(
        select(Scan)
        .where(Scan.project_id == project_id)
        .options(selectinload(Scan.artifacts))
        .order_by(Scan.created_at.desc())
        .limit(1)
    )
    scan = result.scalar_one_or_none()
    if not scan:
        return ContextOut(
            what_happened="Project connected but not scanned yet.",
            who="You pointed Specwright at this codebase.",
            why_it_matters="Undocumented APIs and missing tests cost hours every sprint.",
            what_next="Run a scan to generate OpenAPI, pytest scaffold, and model diagrams.",
        )
    return ContextOut(
        what_happened=scan.summary,
        who=f"Specwright analyzed `{project.root_path}`",
        why_it_matters="Shipping without docs/tests increases incident rate and slows onboarding.",
        what_next="Review generated artifacts, export to repo, wire into CI.",
    )


@router.get("/artifacts/{artifact_id}", response_model=ArtifactOut)
async def get_artifact(artifact_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Artifact).where(Artifact.id == artifact_id).options(selectinload(Artifact.scan))
    )
    art = result.scalar_one_or_none()
    if not art:
        raise HTTPException(404, "Artifact not found")
    return art
