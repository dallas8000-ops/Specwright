import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.models.tables import Scan


async def previous_openapi(db: AsyncSession, project_id: int) -> str | None:
    result = await db.execute(
        select(Scan)
        .where(Scan.project_id == project_id)
        .options(selectinload(Scan.artifacts))
        .order_by(Scan.created_at.desc())
        .limit(1)
    )
    prev = result.scalar_one_or_none()
    if not prev:
        return None
    for a in prev.artifacts:
        if a.kind == "openapi":
            return a.content
    return None


async def previous_openapi_score(db: AsyncSession, project_id: int) -> int | None:
    result = await db.execute(
        select(Scan)
        .where(Scan.project_id == project_id)
        .order_by(Scan.created_at.desc())
        .limit(2)
    )
    scans = result.scalars().all()
    if len(scans) < 2:
        return None
    stats = json.loads(scans[1].stats or "{}")
    return stats.get("score", {}).get("score")
