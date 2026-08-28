"""Regenerate pytest scaffolds for all routes and fill gaps with AI batches."""
from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.analyzers.discovery import collect_python_files, detect_framework
from api.analyzers.django_models import collect_django_model_names
from api.analyzers.route_collector import collect_all_routes
from api.models.tables import Artifact, Project, Scan
from api.services.autopilot import run_post_scan_autopilot
from api.services.health_score import uncovered_routes


async def fix_test_gaps(project: Project, db: AsyncSession) -> dict:
    """Rebuild test scaffold for every route; AI-enhance routes still missing coverage."""
    root = Path(project.root_path).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Path not found: {root}")

    result = await db.execute(
        select(Scan)
        .where(Scan.project_id == project.id)
        .order_by(Scan.id.desc())
        .limit(1)
        .options(selectinload(Scan.artifacts))
    )
    scan = result.scalar_one_or_none()
    if not scan:
        raise LookupError("Run a scan first.")

    files = collect_python_files(root)
    framework = project.framework if project.framework != "auto" else detect_framework(root)
    routes = collect_all_routes(files, root, framework)
    models = collect_django_model_names(files, root)

    tests_art = next((a for a in scan.artifacts if a.kind == "tests"), None)
    if not tests_art:
        tests_art = Artifact(
            scan_id=scan.id,
            kind="tests",
            title="Pytest Scaffold",
            content="",
            file_path="tests/test_generated.py",
        )
        db.add(tests_art)
        await db.flush()

    stats = json.loads(scan.stats or "{}")
    stats.setdefault("framework", framework)
    stats.setdefault("routes_found", len(routes))

    autopilot_patch = await run_post_scan_autopilot(
        project, list(scan.artifacts), routes, stats, root
    )
    stats.update(autopilot_patch)

    gaps_after = len(uncovered_routes(routes, tests_art.content))
    ap = stats.get("autopilot") or {}

    scan.stats = json.dumps(stats)
    await db.flush()

    return {
        "scaffolded_routes": len(routes),
        "gaps_before": ap.get("tests_gaps_before", 0),
        "gaps_after": gaps_after,
        "ai_enhanced": ap.get("tests_ai_enhanced", 0),
        "score": stats.get("score", {}).get("score", 0),
        "synced_files": stats.get("synced_files", []),
        "checks": ap.get("checks", []),
    }
