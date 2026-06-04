"""Watch project folders and re-scan when Python files change."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from api.core.config import settings
from api.core.database import SessionLocal
from api.models.tables import Project, Scan
from api.services.alerts import notify_drift
from api.services.scan_runner import run_scan


def _tree_mtime(root: Path, limit: int = 500) -> float:
    skip = {".venv", "venv", "node_modules", "__pycache__", ".git"}
    latest = 0.0
    count = 0
    for path in root.rglob("*.py"):
        if count >= limit:
            break
        if any(part in skip for part in path.parts):
            continue
        try:
            latest = max(latest, path.stat().st_mtime)
            count += 1
        except OSError:
            continue
    return latest


class WatchManager:
    def __init__(self) -> None:
        self._snapshots: dict[int, float] = {}
        self._queues: dict[int, list[asyncio.Queue[str]]] = {}
        self._task: asyncio.Task | None = None

    def subscribe(self, project_id: int) -> asyncio.Queue[str]:
        q: asyncio.Queue[str] = asyncio.Queue(maxsize=32)
        self._queues.setdefault(project_id, []).append(q)
        return q

    def unsubscribe(self, project_id: int, queue: asyncio.Queue[str]) -> None:
        subs = self._queues.get(project_id, [])
        if queue in subs:
            subs.remove(queue)

    async def _broadcast(self, project_id: int, event: dict) -> None:
        payload = json.dumps(event)
        for q in list(self._queues.get(project_id, [])):
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                pass

    async def _tick(self) -> None:
        async with SessionLocal() as db:
            result = await db.execute(
                select(Project).where(Project.watch_enabled.is_(True))
            )
            projects = result.scalars().all()

            for project in projects:
                root = Path(project.root_path).resolve()
                if not root.exists():
                    continue
                current = _tree_mtime(root)
                prev = self._snapshots.get(project.id)
                self._snapshots[project.id] = current
                if prev is None:
                    continue
                if current <= prev:
                    continue

                await self._broadcast(
                    project.id,
                    {"type": "scan_started", "reason": "files_changed"},
                )
                try:
                    import json

                    from api.services.scan_history import previous_openapi

                    prev = await previous_openapi(db, project.id)
                    scan = await run_scan(
                        project, db, trigger="watch", previous_openapi=prev
                    )
                    stats = json.loads(scan.stats or "{}")
                    score = stats.get("score", {}).get("score", 0)
                    project.last_score = score
                    await db.commit()
                    r2 = await db.execute(
                        select(Scan)
                        .where(Scan.id == scan.id)
                        .options(selectinload(Scan.artifacts))
                    )
                    scan_loaded = r2.scalar_one()
                    drift = stats.get("drift", {})
                    if drift.get("drift_detected"):
                        await notify_drift(
                            project.name,
                            drift.get("message", "Spec drift detected"),
                            score,
                            project.slack_webhook or None,
                        )
                    await self._broadcast(
                        project.id,
                        {
                            "type": "scan_completed",
                            "scan_id": scan_loaded.id,
                            "summary": scan_loaded.summary,
                            "artifact_count": len(scan_loaded.artifacts),
                            "score": stats.get("score"),
                            "coverage": stats.get("coverage"),
                            "synced_files": stats.get("synced_files", []),
                        },
                    )
                except Exception as e:
                    await self._broadcast(
                        project.id,
                        {"type": "scan_failed", "error": str(e)},
                    )

    async def _loop(self) -> None:
        while True:
            try:
                await self._tick()
            except Exception:
                pass
            await asyncio.sleep(settings.watch_interval_seconds)

    def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._loop())


watch_manager = WatchManager()
