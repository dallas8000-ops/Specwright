"""Auto-scan and auto-watch when a project is first connected."""
from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.core.config import settings
from api.models.tables import Scan
from api.services.scan_history import previous_openapi
from api.services.scan_runner import run_scan
from api.services.watch_service import _tree_mtime, watch_manager


async def bootstrap_project(
    db: AsyncSession,
    project,
    *,
    trigger: str = "connect",
    auto_watch: bool | None = None,
    auto_scan: bool | None = None,
) -> Scan | None:
    """Enable watch and/or run the first scan for a newly connected project."""
    watch_on = settings.auto_watch_on_create if auto_watch is None else auto_watch
    scan_on = settings.auto_scan_on_create if auto_scan is None else auto_scan

    if watch_on:
        project.watch_enabled = True
        root = Path(project.root_path).resolve()
        if root.exists():
            watch_manager._snapshots[project.id] = _tree_mtime(root)

    if not scan_on:
        await db.flush()
        return None

    prev = await previous_openapi(db, project.id)
    scan = await run_scan(project, db, trigger=trigger, previous_openapi=prev)
    stats = json.loads(scan.stats or "{}")
    project.last_score = stats.get("score", {}).get("score", 0)
    await db.flush()

    result = await db.execute(
        select(Scan).where(Scan.id == scan.id).options(selectinload(Scan.artifacts))
    )
    return result.scalar_one()
