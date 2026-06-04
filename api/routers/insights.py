import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.core.config import settings
from api.core.database import get_db
from api.models.tables import Artifact, Project, Scan
from api.schemas import CiTemplateOut, HealthOut, NotionPushIn, RoadmapOut, SlackAlertIn
from api.services.alerts import notify_drift
from api.services.ci_template import generate_github_action
from api.services.health_score import build_project_health

router = APIRouter(tags=["insights"])

ROADMAP = [
    {"name": "FastAPI", "status": "live", "detail": "Full route + OpenAPI discovery"},
    {"name": "Django", "status": "live", "detail": "Models, ER diagrams, admin reference"},
    {"name": "Express.js", "status": "planned", "detail": "Decorator + router AST"},
    {"name": "Ruby on Rails", "status": "planned", "detail": "routes.rb + ActiveRecord"},
    {"name": "Laravel", "status": "planned", "detail": "Route list + Eloquent models"},
]


@router.get("/roadmap", response_model=RoadmapOut)
async def product_roadmap():
    return RoadmapOut(
        tagline="The documentation layer for FastAPI teams — automatically.",
        frameworks=ROADMAP,
    )


@router.get("/projects/{project_id}/health", response_model=HealthOut)
async def project_health(project_id: int, db: AsyncSession = Depends(get_db)):
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
        raise HTTPException(404, "Run a scan first")

    stats = json.loads(scan.stats or "{}")
    scanned_at = scan.created_at.isoformat() if scan.created_at else None

    if stats.get("score"):
        coverage = stats.get("coverage", [])
        pr_diff = stats.get("pr_diff")
        if coverage and not coverage[0].get("status_label"):
            from api.services.health_score import enrich_coverage_labels

            coverage = enrich_coverage_labels(
                coverage, added_paths=(pr_diff or {}).get("added_paths")
            )
        return HealthOut(
            score=stats["score"],
            coverage=coverage,
            drift=stats.get("drift", {}),
            pr_diff=pr_diff,
            route_count=stats.get("routes_found", 0),
            models_count=stats.get("models_count", 0),
            metrics=stats.get("metrics"),
            alerts=stats.get("alerts"),
            ai=stats.get("ai"),
            synced_files=stats.get("synced_files", []),
            last_scanned_at=scanned_at,
        )

    from pathlib import Path

    health = build_project_health(Path(project.root_path), scan.artifacts)
    return HealthOut(
        score=health["score"],
        coverage=health["coverage"],
        drift=health["drift"],
        pr_diff=health.get("pr_diff"),
        route_count=health["route_count"],
        models_count=health.get("models_count", 0),
        metrics=health.get("metrics"),
        alerts=health.get("alerts"),
        ai=stats.get("ai"),
        synced_files=stats.get("synced_files", []),
        last_scanned_at=scanned_at,
    )


@router.get("/projects/{project_id}/ci-template", response_model=CiTemplateOut)
async def ci_template(project_id: int, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return CiTemplateOut(
        filename=".github/workflows/specwright.yml",
        content=generate_github_action(),
    )


@router.post("/projects/{project_id}/alerts/slack")
async def configure_slack(
    project_id: int, body: SlackAlertIn, db: AsyncSession = Depends(get_db)
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    project.slack_webhook = body.webhook_url.strip()
    await db.commit()
    return {"ok": True}


@router.post("/projects/{project_id}/alerts/test")
async def test_slack_alert(project_id: int, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    ok = await notify_drift(
        project.name,
        "Test alert from Specwright — drift notifications are configured.",
        project.last_score or 0,
        project.slack_webhook or None,
    )
    if not ok:
        raise HTTPException(400, "Set a Slack webhook URL on the project or SPECWRIGHT_SLACK_WEBHOOK_URL")
    return {"sent": True}


@router.post("/projects/{project_id}/export/notion")
async def push_notion(
    project_id: int, body: NotionPushIn, db: AsyncSession = Depends(get_db)
):
    token = body.notion_token or settings.notion_api_key
    parent = body.parent_page_id or settings.notion_parent_page_id
    if not token or not parent:
        raise HTTPException(
            400,
            "Set SPECWRIGHT_NOTION_API_KEY and SPECWRIGHT_NOTION_PARENT_PAGE_ID, or pass in request body.",
        )

    result = await db.execute(
        select(Scan)
        .where(Scan.project_id == project_id)
        .options(selectinload(Scan.artifacts))
        .order_by(Scan.created_at.desc())
        .limit(1)
    )
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(404, "No scan to export")

    api_md = next((a for a in scan.artifacts if a.kind == "api_docs"), None)
    if not api_md:
        raise HTTPException(404, "No API docs artifact")

    from api.services.notion_export import create_api_docs_page

    try:
        page = await create_api_docs_page(
            token=token,
            parent_page_id=parent,
            title=f"{body.title or 'API Reference'} — Specwright",
            markdown=api_md.content,
        )
    except Exception as e:
        raise HTTPException(502, f"Notion export failed: {e}") from e

    return {"ok": True, "page_url": page.get("url"), "page_id": page.get("id")}
