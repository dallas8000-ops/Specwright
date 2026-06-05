"""Lightweight SQLite migrations for dev (add columns if missing)."""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection


async def run_migrations(conn: AsyncConnection) -> None:
    cols = await _project_columns(conn)
    if "watch_enabled" not in cols:
        await conn.execute(
            text("ALTER TABLE projects ADD COLUMN watch_enabled BOOLEAN DEFAULT 0")
        )
    if "github_repo" not in cols:
        await conn.execute(
            text("ALTER TABLE projects ADD COLUMN github_repo VARCHAR(255) DEFAULT ''")
        )
    if "plan" not in cols:
        await conn.execute(
            text("ALTER TABLE projects ADD COLUMN plan VARCHAR(32) DEFAULT 'starter'")
        )
    if "slack_webhook" not in cols:
        await conn.execute(
            text("ALTER TABLE projects ADD COLUMN slack_webhook VARCHAR(512) DEFAULT ''")
        )
    if "last_score" not in cols:
        await conn.execute(
            text("ALTER TABLE projects ADD COLUMN last_score INTEGER DEFAULT 0")
        )
    if "public_slug" not in cols:
        await conn.execute(
            text("ALTER TABLE projects ADD COLUMN public_slug VARCHAR(64) DEFAULT ''")
        )
    if "badge_public" not in cols:
        await conn.execute(
            text("ALTER TABLE projects ADD COLUMN badge_public BOOLEAN DEFAULT 1")
        )

    scan_cols = await _scan_columns(conn)
    if "trigger" not in scan_cols:
        await conn.execute(
            text("ALTER TABLE scans ADD COLUMN trigger VARCHAR(32) DEFAULT 'manual'")
        )

    art_cols = await _artifact_columns(conn)
    if "polished" not in art_cols:
        await conn.execute(
            text("ALTER TABLE artifacts ADD COLUMN polished BOOLEAN DEFAULT 0")
        )


async def _project_columns(conn: AsyncConnection) -> set[str]:
    r = await conn.execute(text("PRAGMA table_info(projects)"))
    return {row[1] for row in r.fetchall()}


async def _scan_columns(conn: AsyncConnection) -> set[str]:
    r = await conn.execute(text("PRAGMA table_info(scans)"))
    return {row[1] for row in r.fetchall()}


async def _artifact_columns(conn: AsyncConnection) -> set[str]:
    r = await conn.execute(text("PRAGMA table_info(artifacts)"))
    return {row[1] for row in r.fetchall()}
