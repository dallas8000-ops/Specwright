"""Run grounded AI automatically after each scan (Pro + API key)."""
from __future__ import annotations

from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from api.analyzers.fastapi_scanner import _markdown_api
from api.core.config import settings
from api.models.tables import Artifact
from api.services.ai_client import ai_configured
from api.services.ai_descriptions import fill_openapi_descriptions, find_description_gaps
from api.services.ai_docstring_reconcile import _openapi_summaries
from api.services.ai_migration_note import generate_migration_note
from api.services.artifact_sync import sync_artifacts_to_disk
from api.services.health_score import build_project_health
from api.services.scan_history import previous_openapi_score


def _apply_summaries_to_routes(routes: list[dict], openapi: str) -> None:
    spec = _openapi_summaries(openapi)
    for r in routes:
        key = (r["path"], r["method"])
        if key in spec:
            r["summary"] = spec[key]


def _can_auto_ai(plan: str) -> bool:
    return (
        ai_configured()
        and settings.ai_auto_on_scan
        and plan in ("pro", "enterprise")
    )


async def run_post_scan_ai(
    project,
    routes: list[dict],
    artifacts: list[Artifact],
    stats: dict,
    db: AsyncSession,
    *,
    previous_openapi: str | None,
) -> dict:
    """Fill description gaps and generate PR migration notes when eligible."""
    openapi_art = next((a for a in artifacts if a.kind == "openapi"), None)
    api_md_art = next((a for a in artifacts if a.kind == "api_docs"), None)
    openapi = openapi_art.content if openapi_art else ""

    gaps = find_description_gaps(routes, openapi)
    ai_block: dict = {
        "description_gaps": len(gaps),
        "descriptions_filled": 0,
        "migration_note": None,
        "auto_ran": False,
    }

    if not _can_auto_ai(project.plan):
        return {"ai": ai_block}

    ai_block["auto_ran"] = True
    root = Path(project.root_path).resolve()

    if gaps and openapi_art:
        try:
            result = await fill_openapi_descriptions(routes, openapi)
            if result["filled"] > 0:
                openapi_art.content = result["openapi"]
                _apply_summaries_to_routes(routes, result["openapi"])
                if api_md_art:
                    api_md_art.content = _markdown_api(routes)
                ai_block["descriptions_filled"] = result["filled"]
                openapi = result["openapi"]
        except Exception as exc:
            ai_block["description_error"] = str(exc)[:200]

    pr_diff = stats.get("pr_diff")
    if pr_diff and pr_diff.get("routes_changed", 0) > 0:
        try:
            prev_score = await previous_openapi_score(db, project.id)
            note_result = await generate_migration_note(
                pr_diff=pr_diff,
                score=stats.get("score", {}).get("score"),
                previous_score=prev_score,
                project_name=project.name,
            )
            ai_block["migration_note"] = note_result.get("note")
        except Exception as exc:
            ai_block["migration_error"] = str(exc)[:200]

    if ai_block["descriptions_filled"] > 0:
        health = build_project_health(root, artifacts, previous_openapi)
        stats["score"] = health["score"]
        stats["coverage"] = health["coverage"]
        stats["metrics"] = health.get("metrics")
        if project.watch_enabled or stats.get("synced_files") is not None:
            synced = sync_artifacts_to_disk(root, artifacts)
            stats["synced_files"] = synced

    return {"ai": ai_block}
