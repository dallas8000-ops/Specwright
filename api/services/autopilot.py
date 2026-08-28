"""Autopilot — after each scan, close test gaps, resync disk, refresh score/checks."""
from __future__ import annotations

from pathlib import Path

from api.core.config import settings
from api.analyzers.discovery import collect_python_files, detect_framework
from api.analyzers.django_models import collect_django_model_names
from api.analyzers.route_collector import collect_all_routes
from api.analyzers.test_scaffold import generate_tests
from api.models.tables import Artifact
from api.services.ai_client import ai_configured
from api.services.ai_test_bodies import enhance_test_scaffold
from api.services.artifact_sync import sync_artifacts_to_disk
from api.services.health_score import (
    build_alerts,
    build_project_health,
    uncovered_routes,
)


def _checklist(stats: dict, health: dict, *, tests_after: int) -> list[dict]:
    score = health["score"]["score"]
    route_count = stats.get("routes_found") or health.get("route_count") or 0
    metrics = health.get("metrics") or {}
    docs_current = (metrics.get("routes_documented") or {}).get("current", 0)
    docs_total = (metrics.get("routes_documented") or {}).get("total", 0)
    tests_total = (metrics.get("tests_generated") or {}).get("total") or 0
    tests_current = (metrics.get("tests_generated") or {}).get("current", 0)

    if route_count == 0:
        docs_status = "fail"
        tests_status = "fail"
        docs_detail = "0 routes — connect API folder or rescan"
    else:
        docs_status = "pass" if docs_current == docs_total else "warn"
        tests_status = "pass" if tests_after == 0 else "warn"
        docs_detail = f"{docs_current}/{docs_total} routes"
    tests_detail = (
        f"{tests_current}/{tests_total} routes covered"
        if route_count
        else "no routes to cover"
    )

    return [
        {
            "id": "scan",
            "label": "Codebase scan",
            "status": "pass",
        },
        {
            "id": "docs",
            "label": "API documentation",
            "status": docs_status,
            "detail": docs_detail,
        },
        {
            "id": "tests",
            "label": "Test scaffolds",
            "status": tests_status,
            "detail": tests_detail,
        },
        {
            "id": "ci",
            "label": "CI workflow",
            "status": "pass" if stats.get("ci_synced") else "skip",
            "detail": ".github/workflows/specwright.yml",
        },
        {
            "id": "score",
            "label": "Specwright Score",
            "status": "pass" if score >= 80 else "warn" if score >= 60 else "fail",
            "detail": f"{score}/100",
        },
    ]


async def run_post_scan_autopilot(
    project,
    artifact_rows: list[Artifact],
    routes: list[dict],
    stats: dict,
    root: Path,
) -> dict:
    """
    Finish checks automatically: scaffold missing tests, AI-enhance gaps, resync, refresh score.
    Runs at end of every scan when autopilot_mode is on (default).
    """
    if not settings.autopilot_mode:
        return {}

    tests_art = next((a for a in artifact_rows if a.kind == "tests"), None)
    if not tests_art:
        return {}

    framework = stats.get("framework", project.framework)
    if framework == "auto":
        framework = detect_framework(root)

    gaps_before = len(uncovered_routes(routes, tests_art.content))
    ai_enhanced = 0

    # Regenerate full scaffold if anything is missing (idempotent).
    if gaps_before > 0:
        files = collect_python_files(root)
        models = collect_django_model_names(files, root)
        tests_art.content = generate_tests(
            framework=framework,
            routes=routes,
            models=models,
            project_name=project.name,
        )
        gaps_before = len(uncovered_routes(routes, tests_art.content))

    can_ai = (
        ai_configured()
        and settings.ai_auto_tests_on_scan
        and project.plan in ("pro", "enterprise")
    )
    missing = uncovered_routes(routes, tests_art.content)
    if can_ai and missing:
        files = collect_python_files(root)
        models = collect_django_model_names(files, root)
        result = await enhance_test_scaffold(
            framework=framework,
            routes=missing,
            models=models,
            project_name=project.name,
            root=root,
            base_content=tests_art.content,
        )
        tests_art.content = result["content"]
        ai_enhanced = result["enhanced"]

    gaps_after = len(uncovered_routes(routes, tests_art.content))

    # Push updated artifacts to repo and refresh score/alerts.
    synced = sync_artifacts_to_disk(root, artifact_rows)
    if synced:
        existing = list(stats.get("synced_files") or [])
        for path in synced:
            if path not in existing:
                existing.append(path)
        stats["synced_files"] = existing

    health = build_project_health(root, artifact_rows, None)
    stats["score"] = health["score"]
    stats["coverage"] = health["coverage"]
    stats["metrics"] = health.get("metrics")
    stats["alerts"] = build_alerts(
        stats["coverage"],
        stats.get("pr_diff"),
        ai=stats.get("ai"),
        route_count=health.get("route_count"),
        framework=framework,
    )

    checks = _checklist(stats, health, tests_after=gaps_after)
    route_count = stats.get("routes_found") or len(health.get("coverage") or [])
    all_pass = (
        all(c["status"] in ("pass", "skip") for c in checks)
        and route_count > 0
        and health["score"]["score"] >= 60
    )
    project.last_score = health["score"]["score"]

    return {
        "autopilot": {
            "enabled": True,
            "tests_gaps_before": gaps_before,
            "tests_gaps_after": gaps_after,
            "tests_ai_enhanced": ai_enhanced,
            "checks": checks,
            "all_pass": all_pass,
            "route_count": route_count,
        }
    }


async def run_full_autopilot(project, db) -> dict:
    """Rescan + autopilot in one call (for API / fix-tests endpoint reuse)."""
    from api.services.scan_history import previous_openapi
    from api.services.scan_runner import run_scan

    prev = await previous_openapi(db, project.id)
    scan = await run_scan(project, db, previous_openapi=prev)
    import json

    stats = json.loads(scan.stats or "{}")
    return {
        "scan_id": scan.id,
        "summary": scan.summary,
        "autopilot": stats.get("autopilot"),
        "score": stats.get("score", {}).get("score"),
    }
