"""Run grounded AI automatically after each scan (Pro + API key)."""
from __future__ import annotations

from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from api.analyzers.discovery import collect_python_files
from api.analyzers.fastapi_scanner import _markdown_api
from api.core.config import settings
from api.models.tables import Artifact
from api.services.ai_client import ai_configured
from api.services.ai_descriptions import fill_openapi_descriptions, find_description_gaps
from api.services.ai_docstring_reconcile import _openapi_summaries
from api.services.ai_migration_note import generate_migration_note
from api.services.ai_test_bodies import enhance_test_scaffold
from api.services.artifact_sync import sync_artifacts_to_disk
from api.services.health_score import build_project_health
from api.services.scan_history import previous_openapi_score
from api.analyzers.django_models import collect_django_model_names


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


def _refresh_health_and_sync(
    project,
    artifacts: list[Artifact],
    stats: dict,
    root: Path,
    previous_openapi: str | None,
) -> None:
    health = build_project_health(root, artifacts, previous_openapi)
    stats["score"] = health["score"]
    stats["coverage"] = health["coverage"]
    stats["metrics"] = health.get("metrics")
    if project.watch_enabled or stats.get("synced_files") is not None:
        stats["synced_files"] = sync_artifacts_to_disk(root, artifacts)


async def run_post_scan_ai(
    project,
    routes: list[dict],
    artifacts: list[Artifact],
    stats: dict,
    db: AsyncSession,
    *,
    previous_openapi: str | None,
) -> dict:
    """Fill descriptions, enhance tests, and generate PR migration notes when eligible."""
    openapi_art = next((a for a in artifacts if a.kind == "openapi"), None)
    api_md_art = next((a for a in artifacts if a.kind == "api_docs"), None)
    tests_art = next((a for a in artifacts if a.kind == "tests"), None)
    openapi = openapi_art.content if openapi_art else ""

    gaps = find_description_gaps(routes, openapi)
    ai_block: dict = {
        "description_gaps": len(gaps),
        "descriptions_filled": 0,
        "tests_enhanced": 0,
        "migration_note": None,
        "auto_ran": False,
    }

    if not _can_auto_ai(project.plan):
        return {"ai": ai_block}

    ai_block["auto_ran"] = True
    root = Path(project.root_path).resolve()
    artifacts_changed = False

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
                artifacts_changed = True
        except Exception as exc:
            ai_block["description_error"] = str(exc)[:200]

    if settings.ai_auto_tests_on_scan and tests_art:
        try:
            files = collect_python_files(root)
            models = collect_django_model_names(files, root)
            framework = stats.get("framework", project.framework)
            from api.services.health_score import compute_coverage_map

            rows = compute_coverage_map(routes, tests_art.content, "", "")
            missing_keys = {(r["method"], r["path"]) for r in rows if not r["has_test"]}
            missing_routes = [
                r for r in routes if (r.get("method"), r.get("path")) in missing_keys
            ]
            test_result = await enhance_test_scaffold(
                framework=framework,
                routes=missing_routes or routes,
                models=models,
                project_name=project.name,
                root=root,
                base_content=tests_art.content,
            )
            if test_result["enhanced"] > 0 or missing_routes:
                tests_art.content = test_result["content"]
                ai_block["tests_enhanced"] = test_result["enhanced"]
                artifacts_changed = True
        except Exception as exc:
            ai_block["tests_error"] = str(exc)[:200]

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

    if artifacts_changed:
        _refresh_health_and_sync(project, artifacts, stats, root, previous_openapi)

    return {"ai": ai_block}
