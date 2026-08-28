from pathlib import Path

from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import settings


def _ensure_sqlite_parent_dir(database_url: str) -> None:
    """Create parent dirs for file-based SQLite (e.g. tmp/ on Render)."""
    url = make_url(database_url)
    if not url.drivername.startswith("sqlite"):
        return
    db_file = url.database
    if not db_file or db_file == ":memory:":
        return
    db_path = Path(db_file)
    if not db_path.is_absolute():
        db_path = Path.cwd() / db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)


def _sqlite_connect_args(database_url: str) -> dict:
    if not make_url(database_url).drivername.startswith("sqlite"):
        return {}
    return {"timeout": 30}


_ensure_sqlite_parent_dir(settings.database_url)
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    connect_args=_sqlite_connect_args(settings.database_url),
)

SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with SessionLocal() as session:
        yield session


async def init_db():
    import asyncio

    from sqlalchemy import text

    from api.core.migrate import run_migrations
    from api.models import tables  # noqa: F401
    from api.services.project_slug import backfill_project_slugs

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await run_migrations(conn)

    if settings.database_url.startswith("sqlite"):
        for attempt in range(6):
            try:
                async with engine.connect() as conn:
                    await conn.execute(text("PRAGMA busy_timeout=30000"))
                    await conn.execute(text("PRAGMA journal_mode=WAL"))
                    await conn.commit()
                break
            except Exception:
                if attempt >= 5:
                    break
                await asyncio.sleep(0.4 * (attempt + 1))

    async with SessionLocal() as session:
        await backfill_project_slugs(session)
