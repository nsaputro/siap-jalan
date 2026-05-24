from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.future import select

from .database import AsyncSessionLocal, Base, engine
from .models.packing import ActivityTemplate, ActivityTemplateItem
from .routers import activities, ai, packing, templates, trips

# Seed file: look next to cwd or one level up (handles both direct & Docker runs)
_CANDIDATE_SEED_PATHS = [
    Path("data/activity_templates.json"),
    Path("../data/activity_templates.json"),
    Path("/app/data/activity_templates.json"),
]


def _find_seed_path() -> Path | None:
    for p in _CANDIDATE_SEED_PATHS:
        if p.exists():
            return p
    return None


async def _seed_activities() -> None:
    seed = _find_seed_path()
    if seed is None:
        return

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(ActivityTemplate).limit(1))
        if result.scalar_one_or_none() is not None:
            return  # already seeded

        data = json.loads(seed.read_text(encoding="utf-8"))
        for entry in data:
            items_data = entry.pop("items", [])
            at = ActivityTemplate(is_builtin=True, ha_user_id=None, **entry)
            db.add(at)
            await db.flush()
            for item in items_data:
                db.add(ActivityTemplateItem(activity_template_id=at.id, **item))
        await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[type-arg]
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _seed_activities()
    yield


app = FastAPI(title="SiapJalan", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trips.router)
app.include_router(packing.router)
app.include_router(activities.router)
app.include_router(templates.router)
app.include_router(ai.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
