"""Pure unit tests for the activity_merger service (uses real in-memory DB)."""
from __future__ import annotations

import pytest
from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.database import Base
from app.models.packing import ActivityTemplate, ActivityTemplateItem
from app.services.activity_merger import merge_activities

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def seeded_session():
    """In-memory DB pre-loaded with hiking + beach templates."""
    engine = create_async_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        hiking = ActivityTemplate(slug="hiking", name="Hiking", icon_emoji="🥾", is_builtin=True, climate_types=[])
        beach = ActivityTemplate(slug="beach", name="Beach", icon_emoji="🏖️", is_builtin=True, climate_types=[])
        session.add_all([hiking, beach])
        await session.flush()

        session.add_all([
            # Hiking items
            ActivityTemplateItem(activity_template_id=hiking.id, category="Clothing",            name="Trail shoes", quantity=1, is_essential=True,  priority=8),
            ActivityTemplateItem(activity_template_id=hiking.id, category="Other",            name="Headlamp",   quantity=1, is_essential=False, priority=5),
            ActivityTemplateItem(activity_template_id=hiking.id, category="Toiletries & Hygiene", name="Sunscreen", quantity=1, is_essential=False, priority=4),
            # Beach items
            ActivityTemplateItem(activity_template_id=beach.id,  category="Clothing",            name="Swimwear",   quantity=1, is_essential=True,  priority=8),
            ActivityTemplateItem(activity_template_id=beach.id,  category="Toiletries & Hygiene", name="Sunscreen", quantity=2, is_essential=True,  priority=6),  # higher qty + essential
            ActivityTemplateItem(activity_template_id=beach.id,  category="Shoes & Accessories", name="Flip flops", quantity=1, is_essential=False, priority=3),
        ])
        await session.commit()
        yield session

    await engine.dispose()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

async def test_merge_empty_slugs(seeded_session):
    result = await merge_activities(seeded_session, [])
    assert result == []


async def test_merge_unknown_slug_returns_empty(seeded_session):
    result = await merge_activities(seeded_session, ["nonexistent_xyz"])
    assert result == []


async def test_merge_single_activity_returns_all_items(seeded_session):
    result = await merge_activities(seeded_session, ["hiking"])
    assert len(result) == 3
    names = {r.name for r in result}
    assert names == {"Trail shoes", "Headlamp", "Sunscreen"}


async def test_merge_two_activities_deduplicates_sunscreen(seeded_session):
    result = await merge_activities(seeded_session, ["hiking", "beach"])
    names = [r.name for r in result]
    assert names.count("Sunscreen") == 1, "Sunscreen should appear only once"
    assert len(result) == 5  # Trail shoes, Headlamp, Sunscreen, Swimwear, Flip flops


async def test_essential_or_logic(seeded_session):
    """Sunscreen is not essential in hiking but IS essential in beach → merged = essential."""
    result = await merge_activities(seeded_session, ["hiking", "beach"])
    sunscreen = next(r for r in result if r.name == "Sunscreen")
    assert sunscreen.is_essential is True


async def test_quantity_is_max_across_sources(seeded_session):
    """Sunscreen qty=1 in hiking, qty=2 in beach → merged qty=2."""
    result = await merge_activities(seeded_session, ["hiking", "beach"])
    sunscreen = next(r for r in result if r.name == "Sunscreen")
    assert sunscreen.quantity == 2


async def test_source_activities_accumulated(seeded_session):
    """Sunscreen comes from both hiking and beach → both slugs in source_activities."""
    result = await merge_activities(seeded_session, ["hiking", "beach"])
    sunscreen = next(r for r in result if r.name == "Sunscreen")
    assert set(sunscreen.source_activities) == {"hiking", "beach"}


async def test_non_overlapping_items_keep_single_source(seeded_session):
    result = await merge_activities(seeded_session, ["hiking", "beach"])
    headlamp = next(r for r in result if r.name == "Headlamp")
    assert headlamp.source_activities == ["hiking"]
    flipflops = next(r for r in result if r.name == "Flip flops")
    assert flipflops.source_activities == ["beach"]


async def test_result_sorted_by_category_then_name(seeded_session):
    result = await merge_activities(seeded_session, ["hiking", "beach"])
    pairs = [(r.category, r.name) for r in result]
    assert pairs == sorted(pairs)


async def test_dedup_is_case_insensitive(seeded_session):
    """Add a duplicate with different casing; should still deduplicate."""
    # Add SUNSCREEN directly via the existing session (avoids get_bind() on async session)
    hiking_r = await seeded_session.execute(
        sa_select(ActivityTemplate).where(ActivityTemplate.slug == "hiking")
    )
    hiking = hiking_r.scalar_one()
    seeded_session.add(ActivityTemplateItem(
        activity_template_id=hiking.id,
        category="Toiletries & Hygiene",
        name="SUNSCREEN",   # upper-case duplicate
        quantity=1, is_essential=False, priority=2,
    ))
    await seeded_session.commit()

    result = await merge_activities(seeded_session, ["hiking"])
    sunscreen_hits = [r for r in result if r.name.lower() == "sunscreen"]
    assert len(sunscreen_hits) == 1


async def test_template_item_id_set_on_merged_item(seeded_session):
    result = await merge_activities(seeded_session, ["hiking"])
    for item in result:
        assert item.template_item_id is not None
