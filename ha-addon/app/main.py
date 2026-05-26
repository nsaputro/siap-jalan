from __future__ import annotations

import json
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.future import select

from .database import AsyncSessionLocal, Base, engine
from .models.packing import ActivityTemplate, ActivityTemplateItem
from .routers import activities, ai, packing, templates, trips


STATIC_DIR = Path("/app/static")
DATA_FILE = Path("/app/data/activity_templates.json")


async def seed_activity_templates() -> None:
    """Seed built-in activity templates from JSON file if table is empty."""
    if not DATA_FILE.exists():
        return

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(ActivityTemplate).limit(1))
        existing = result.scalar_one_or_none()
        if existing:
            return

        try:
            data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except Exception:
            return

        for tmpl_data in data:
            items_data = tmpl_data.pop("items", [])
            tmpl = ActivityTemplate(
                is_builtin=True,
                ha_user_id=None,
                **{k: v for k, v in tmpl_data.items()},
            )
            db.add(tmpl)
            await db.flush()

            for item_data in items_data:
                item = ActivityTemplateItem(
                    activity_template_id=tmpl.id,
                    **item_data,
                )
                db.add(item)

        await db.commit()


async def _run_migrations() -> None:
    """Apply additive schema migrations for columns added after initial release."""
    migrations = [
        "ALTER TABLE activity_template_items ADD COLUMN is_hidden BOOLEAN NOT NULL DEFAULT 0",
        "ALTER TABLE activity_template_items ADD COLUMN is_user_added BOOLEAN NOT NULL DEFAULT 0",
    ]
    async with engine.begin() as conn:
        for stmt in migrations:
            try:
                await conn.execute(text(stmt))
            except Exception:
                pass  # column already exists — safe to ignore


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _run_migrations()
    await seed_activity_templates()
    yield


app = FastAPI(title="SiapJalan HA Addon", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routers — registered BEFORE static/catch-all
app.include_router(trips.router)
app.include_router(packing.router)
app.include_router(activities.router)
app.include_router(templates.router)
app.include_router(ai.router)

# Static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def catch_all(full_path: str):
        index = STATIC_DIR / "index.html"
        if index.exists():
            return FileResponse(str(index))
        return {"detail": "Not found"}
