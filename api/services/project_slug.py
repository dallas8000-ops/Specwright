"""Public slug for embeddable score badges."""
from __future__ import annotations

import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.tables import Project


def new_public_slug() -> str:
    return f"project-{secrets.token_hex(6)}"


async def ensure_unique_slug(db: AsyncSession, base: str | None = None) -> str:
    for _ in range(10):
        slug = base or new_public_slug()
        existing = await db.execute(select(Project.id).where(Project.public_slug == slug).limit(1))
        if not existing.scalar_one_or_none():
            return slug
        base = None
    return new_public_slug()


async def backfill_project_slugs(db: AsyncSession) -> None:
    result = await db.execute(select(Project).where(Project.public_slug == ""))
    for project in result.scalars().all():
        project.public_slug = await ensure_unique_slug(db)
    await db.commit()
