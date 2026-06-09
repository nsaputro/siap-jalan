"""
Shared pytest fixtures.

Strategy
--------
`app.main` imports `engine` and `AsyncSessionLocal` by name at import time,
so patching only `app.database` is not enough.  We patch all three locations
before the ASGI lifespan starts:

    app.database.engine           (used by get_db and lifespan via module ref)
    app.database.AsyncSessionLocal
    app.main.engine               (captured by the lifespan at import time)
    app.main.AsyncSessionLocal    (captured by _seed_activities at import time)
"""
from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.database as db_module
import app.main as main_module
from app.database import Base, get_db
from app.dependencies import get_ha_user
from app.main import app as fastapi_app
from app.models.packing import ActivityTemplate, ActivityTemplateItem

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

# Path to seed data (relative to backend/ working directory)
_SEED_CANDIDATES = [
    Path("../data/activity_templates.json"),
    Path("data/activity_templates.json"),
]


async def _seed(factory: async_sessionmaker) -> None:
    """Load activity templates from the JSON seed file into the test DB."""
    seed_path = next((p for p in _SEED_CANDIDATES if p.exists()), None)
    if seed_path is None:
        return

    data = json.loads(seed_path.read_text())
    async with factory() as session:
        for entry in data:
            items_data = entry.pop("items", [])
            at = ActivityTemplate(is_builtin=True, ha_user_id=None, **entry)
            session.add(at)
            await session.flush()
            for item in items_data:
                session.add(ActivityTemplateItem(activity_template_id=at.id, **item))
        await session.commit()


@pytest.fixture
async def client():
    """Full ASGI test client backed by an isolated in-memory SQLite DB.

    Patches db_module AND main_module so the lifespan and seeding use the
    test engine instead of the real file-based DB.
    """
    test_engine = create_async_engine(TEST_DB_URL)
    test_factory = async_sessionmaker(test_engine, expire_on_commit=False)

    # Create tables and seed BEFORE the lifespan runs so the lifespan's
    # own create_all + seed calls are idempotent (table exists, table non-empty).
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _seed(test_factory)

    # Patch every reference to engine / AsyncSessionLocal used by the app
    orig = {
        "db_engine":   db_module.engine,
        "db_factory":  db_module.AsyncSessionLocal,
        "main_engine": main_module.engine,
        "main_factory": main_module.AsyncSessionLocal,
    }
    db_module.engine = test_engine
    db_module.AsyncSessionLocal = test_factory
    main_module.engine = test_engine
    main_module.AsyncSessionLocal = test_factory

    async def _override_db() -> AsyncSession:  # type: ignore[override]
        async with test_factory() as session:
            yield session

    fastapi_app.dependency_overrides[get_db] = _override_db

    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app), base_url="http://test"
    ) as ac:
        yield ac

    fastapi_app.dependency_overrides.clear()
    db_module.engine = orig["db_engine"]
    db_module.AsyncSessionLocal = orig["db_factory"]
    main_module.engine = orig["main_engine"]
    main_module.AsyncSessionLocal = orig["main_factory"]
    await test_engine.dispose()


@pytest.fixture
def as_user(client: AsyncClient):  # noqa: F811
    """Context manager that temporarily overrides the active HA user.

    Usage::

        async def test_foo(client, as_user):
            with as_user("user_a"):
                r = await client.post("/activities", json=...)
            with as_user("user_b"):
                r2 = await client.put(...)
    """
    @contextmanager
    def _set_user(user_id: str) -> Generator[None, None, None]:
        fastapi_app.dependency_overrides[get_ha_user] = lambda: user_id
        try:
            yield
        finally:
            fastapi_app.dependency_overrides.pop(get_ha_user, None)

    return _set_user


@pytest.fixture
async def db_session():
    """Bare async DB session against an in-memory DB (no HTTP, no seeding).
    Used by pure unit tests."""
    test_engine = create_async_engine(TEST_DB_URL)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with factory() as session:
        yield session

    await test_engine.dispose()


def trip_payload(**overrides: object) -> dict:
    import datetime
    start = datetime.date.today() + datetime.timedelta(days=30)
    end = start + datetime.timedelta(days=6)
    return {
        "destination": "Bali",
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "traveller_count": 1,
        **overrides,
    }
