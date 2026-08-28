"""Load latest scan artifacts for AI endpoints."""
from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.analyzers.discovery import collect_python_files, detect_framework
from api.analyzers.route_collector import collect_all_routes
from api.models.tables import Project, Scan


async def load_project_scan_context(
    db: AsyncSession, project_id: int
) -> tuple[Project, Scan, dict, list[dict]]:
    project = await db.get(Project, project_id)
    if not project:
        raise LookupError("Project not found")

    result = await db.execute(
        select(Scan)
        .where(Scan.project_id == project_id)
        .options(selectinload(Scan.artifacts))
        .order_by(Scan.created_at.desc())
        .limit(1)
    )
    scan = result.scalar_one_or_none()
    if not scan:
        raise LookupError("Run a scan first")

    stats = json.loads(scan.stats or "{}")
    by_kind = {a.kind: a.content for a in scan.artifacts}

    root = Path(project.root_path).resolve()
    files = collect_python_files(root)
    framework = project.framework if project.framework != "auto" else detect_framework(root)
    routes = collect_all_routes(files, root, framework)

    return project, scan, stats, routes, by_kind
