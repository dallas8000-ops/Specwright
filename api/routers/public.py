"""Public embeds — score badges for GitHub READMEs (no auth)."""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.config import settings
from api.core.database import get_db
from api.models.tables import Project, Scan
from api.schemas import BadgeEmbedOut, PublicProjectOut
from api.services.badge_svg import render_score_badge

router = APIRouter(tags=["public"])


def _badge_image_url(slug: str) -> str:
    base = settings.public_api_url.rstrip("/")
    return f"{base}/api/v1/badge/{slug}.svg"


def _project_link(slug: str, project_id: int) -> str:
    return f"{settings.public_site_url.rstrip('/')}/api/v1/p/{slug}"


def _markdown_embed(slug: str, project_id: int, score: int | None) -> str:
    img = _badge_image_url(slug)
    link = _project_link(slug, project_id)
    alt = f"Specwright Score {score}" if score is not None else "Specwright Score"
    return f"[![{alt}]({img})]({link})"


async def _project_by_slug(db: AsyncSession, slug: str) -> Project | None:
    result = await db.execute(select(Project).where(Project.public_slug == slug).limit(1))
    return result.scalar_one_or_none()


def _score_from_project(project: Project, latest_stats: dict) -> int | None:
    score_obj = latest_stats.get("score") or {}
    if score_obj.get("score") is not None:
        return int(score_obj["score"])
    if project.last_score:
        return project.last_score
    return None


@router.get("/badge/{slug}.svg", response_class=Response)
async def public_badge_svg(slug: str, db: AsyncSession = Depends(get_db)):
    project = await _project_by_slug(db, slug)
    if not project or not project.badge_public:
        svg = render_score_badge(score=None, label="Specwright")
        return Response(
            content=svg,
            media_type="image/svg+xml",
            headers={"Cache-Control": "public, max-age=60"},
        )

    scan_result = await db.execute(
        select(Scan)
        .where(Scan.project_id == project.id, Scan.status == "completed")
        .order_by(Scan.created_at.desc())
        .limit(1)
    )
    latest = scan_result.scalar_one_or_none()
    stats = json.loads(latest.stats or "{}") if latest else {}
    score = _score_from_project(project, stats)

    svg = render_score_badge(score=score)
    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={"Cache-Control": "public, max-age=300"},
    )


@router.get("/public/projects/{slug}", response_model=PublicProjectOut)
async def public_project_card(slug: str, db: AsyncSession = Depends(get_db)):
    project = await _project_by_slug(db, slug)
    if not project:
        raise HTTPException(404, "Project not found")
    scan_result = await db.execute(
        select(Scan)
        .where(Scan.project_id == project.id, Scan.status == "completed")
        .order_by(Scan.created_at.desc())
        .limit(1)
    )
    latest = scan_result.scalar_one_or_none()
    stats = json.loads(latest.stats or "{}") if latest else {}
    score = _score_from_project(project, stats)
    return PublicProjectOut(
        slug=slug,
        name=project.name,
        score=score,
        grade=(stats.get("score") or {}).get("grade"),
        framework=project.framework,
        routes_found=stats.get("routes_found", 0),
        last_scanned_at=latest.created_at.isoformat() if latest and latest.created_at else None,
        project_url=f"{settings.frontend_url.rstrip('/')}/project/{project.id}",
    )


@router.get("/projects/{project_id}/badge-embed", response_model=BadgeEmbedOut)
async def project_badge_embed(project_id: int, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    if not project.public_slug:
        from api.services.project_slug import ensure_unique_slug

        project.public_slug = await ensure_unique_slug(db)
        await db.commit()
        await db.refresh(project)

    scan_result = await db.execute(
        select(Scan)
        .where(Scan.project_id == project.id, Scan.status == "completed")
        .order_by(Scan.created_at.desc())
        .limit(1)
    )
    latest = scan_result.scalar_one_or_none()
    stats = json.loads(latest.stats or "{}") if latest else {}
    score = _score_from_project(project, stats)
    slug = project.public_slug

    return BadgeEmbedOut(
        public_slug=slug,
        score=score,
        badge_enabled=project.badge_public,
        image_url=_badge_image_url(slug),
        project_url=_project_link(slug, project.id),
        markdown=_markdown_embed(slug, project.id, score),
        hosted_image_url=f"https://specwright.app/badge/{slug}.svg",
        hosted_project_url=f"https://specwright.app/p/{slug}",
    )


@router.get("/p/{slug}", include_in_schema=False, response_class=HTMLResponse)
async def public_landing_redirect(slug: str, db: AsyncSession = Depends(get_db)):
    """Lightweight landing when someone clicks a README badge."""
    project = await _project_by_slug(db, slug)
    if not project:
        raise HTTPException(404, "Project not found")
    scan_result = await db.execute(
        select(Scan)
        .where(Scan.project_id == project.id, Scan.status == "completed")
        .order_by(Scan.created_at.desc())
        .limit(1)
    )
    latest = scan_result.scalar_one_or_none()
    stats = json.loads(latest.stats or "{}") if latest else {}
    score = _score_from_project(project, stats)
    score_display = score if score is not None else "—"
    color = "#22c55e" if score and score >= 85 else "#eab308" if score and score >= 65 else "#ef4444"
    app_url = settings.frontend_url.rstrip("/")
    return HTMLResponse(
        f"""<!DOCTYPE html>
<html lang="en"><head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>{project.name} — Specwright Score</title>
  <style>
    body {{ font-family: system-ui, sans-serif; background: #0f1419; color: #f1f5f9;
      display: grid; place-items: center; min-height: 100vh; margin: 0; padding: 1.5rem; }}
    .card {{ max-width: 420px; text-align: center; padding: 2rem; background: #1c2638;
      border: 1px solid #2d3f5c; border-radius: 14px; }}
    .score {{ font-size: 3rem; font-weight: 800; color: {color}; }}
    a {{ color: #22d3ee; font-weight: 600; }}
    p {{ color: #94a3b8; line-height: 1.5; }}
  </style>
</head>
<body>
  <div class="card">
    <p>Specwright Score</p>
    <div class="score">{score_display}</div>
    <h1 style="font-size:1.25rem;margin:1rem 0 0.5rem">{project.name}</h1>
    <p>API documentation health from your codebase — AST-grounded, not guessed.</p>
    <p style="margin-top:1.25rem"><a href="{app_url}/project/{project.id}">Open full report →</a></p>
    <p style="margin-top:1rem;font-size:0.85rem"><a href="{app_url}">Get Specwright for your APIs</a></p>
  </div>
</body></html>"""
    )
