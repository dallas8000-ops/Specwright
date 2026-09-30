"""Shared fixtures for the API test suite.

The app creates its schema in the FastAPI lifespan (``init_db``), which only
runs when a TestClient is used as a context manager. Most tests construct
``TestClient(app)`` directly, so without this the suite hits
"no such table: projects". Point the app at an isolated SQLite file and build
the schema once per session instead.
"""
import asyncio
import os
import tempfile
from pathlib import Path

# Must be set before api.core.config / api.core.database are imported: the
# engine is created at import time from settings.database_url.
_TEST_DB = Path(tempfile.mkdtemp(prefix="specwright-tests-")) / "test.db"
os.environ["SPECWRIGHT_DATABASE_URL"] = f"sqlite+aiosqlite:///{_TEST_DB}"
os.environ.setdefault("SPECWRIGHT_DEBUG", "false")

import pytest  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _initialise_schema():
    from api.core.database import engine, init_db

    async def _init():
        await init_db()
        # Drop pooled connections bound to this temporary event loop so later
        # tests (TestClient / anyio) open fresh ones on their own loop.
        await engine.dispose()

    asyncio.run(_init())
    yield
