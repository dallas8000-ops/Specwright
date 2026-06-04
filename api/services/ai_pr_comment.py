"""Enrich GitHub PR comments with grounded AI insights when configured."""
from __future__ import annotations

from api.core.config import settings
from api.services.ai_breaking_change import classify_pr_diff
from api.services.ai_client import ai_configured
from api.services.ai_docstring_reconcile import reconcile_docstrings
from api.services.ai_migration_note import generate_migration_note
from api.services.scan_history import previous_openapi_score
from sqlalchemy.ext.asyncio import AsyncSession


async def enrich_pr_comment_context(
    db: AsyncSession,
    *,
    project_id: int,
    project_name: str,
    plan: str,
    stats: dict,
    routes: list[dict],
    openapi: str,
) -> dict:
    triage = stats.get("breaking_change") or classify_pr_diff(stats.get("pr_diff"))
    reconcile_count = len(reconcile_docstrings(routes, openapi))
    migration_note = None

    if ai_configured() and plan in ("pro", "enterprise") and stats.get("pr_diff"):
        prev_score = await previous_openapi_score(db, project_id)
        try:
            result = await generate_migration_note(
                pr_diff=stats.get("pr_diff"),
                score=stats.get("score", {}).get("score"),
                previous_score=prev_score,
                project_name=project_name,
            )
            migration_note = result.get("note")
        except Exception:
            migration_note = None

    return {
        "breaking_triage": triage,
        "migration_note": migration_note,
        "reconcile_count": reconcile_count,
    }
