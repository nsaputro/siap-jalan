"""Unit tests for template_propagation service (in-memory DB, no HTTP)."""
from __future__ import annotations

import datetime

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.future import select

from app.database import Base
from app.models.packing import (
    ActivityTemplate,
    ActivityTemplateItem,
    PackingItem,
    PackingList,
    Trip,
)
from app.services.template_propagation import propagate_template_change

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
TODAY = datetime.date.today()
FUTURE = TODAY + datetime.timedelta(days=30)
PAST = TODAY - datetime.timedelta(days=1)


@pytest.fixture
async def session():
    engine = create_async_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        yield s
    await engine.dispose()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def make_template(session, slug="test_act") -> tuple[ActivityTemplate, ActivityTemplateItem]:
    tmpl = ActivityTemplate(slug=slug, name="Test", icon_emoji="🧪", is_builtin=False, climate_types=[])
    session.add(tmpl)
    await session.flush()
    item = ActivityTemplateItem(
        activity_template_id=tmpl.id,
        name="Prop Item",
        quantity=1, is_essential=False, priority=5,
    )
    session.add(item)
    await session.flush()
    return tmpl, item


async def make_trip(session, slug="test_act", end_date=FUTURE) -> tuple[Trip, PackingList]:
    trip = Trip(
        destination="Testville",
        start_date=TODAY,
        end_date=end_date,
        activities=[slug],
        traveller_count=1,
    )
    session.add(trip)
    await session.flush()
    plist = PackingList(trip_id=trip.id, name="Main", is_default=True)
    session.add(plist)
    await session.flush()
    return trip, plist


async def make_packing_item(session, list_id, template_item_id=None, name="Prop Item", is_customised=False, is_packed=False) -> PackingItem:
    pi = PackingItem(
        list_id=list_id,
        name=name,
        quantity=1, is_essential=False,
        added_by="activity",
        source_activities=["test_act"],
        template_item_id=template_item_id,
        is_customised=is_customised,
        is_packed=is_packed,
    )
    session.add(pi)
    await session.flush()
    return pi


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

async def test_adds_item_to_active_trip(session):
    tmpl, tmpl_item = await make_template(session)
    _, plist = await make_trip(session)
    await session.commit()

    summary = await propagate_template_change(
        session, tmpl.id,
        added_items=[tmpl_item], updated_items=[], removed_item_ids=[], today=TODAY,
    )

    result = await session.execute(select(PackingItem).where(PackingItem.list_id == plist.id))
    items = result.scalars().all()
    assert len(items) == 1
    assert items[0].name == "Prop Item"
    assert summary["items_added"] == 1
    assert summary["trips_updated"] == 1


async def test_skips_add_if_name_already_exists(session):
    tmpl, tmpl_item = await make_template(session)
    _, plist = await make_trip(session)
    await make_packing_item(session, plist.id, name="Prop Item")  # same name already present
    await session.commit()

    summary = await propagate_template_change(
        session, tmpl.id,
        added_items=[tmpl_item], updated_items=[], removed_item_ids=[], today=TODAY,
    )
    assert summary["items_added"] == 0

    result = await session.execute(select(PackingItem).where(PackingItem.list_id == plist.id))
    assert len(result.scalars().all()) == 1  # no duplicate


async def test_updates_non_customised_item(session):
    tmpl, tmpl_item = await make_template(session)
    _, plist = await make_trip(session)
    pi = await make_packing_item(session, plist.id, template_item_id=tmpl_item.id, name="Prop Item")
    await session.commit()

    tmpl_item.name = "Updated Name"
    summary = await propagate_template_change(
        session, tmpl.id,
        added_items=[], updated_items=[tmpl_item], removed_item_ids=[], today=TODAY,
    )

    await session.refresh(pi)
    assert pi.name == "Updated Name"
    assert summary["items_updated"] == 1


async def test_skips_customised_item_on_update(session):
    tmpl, tmpl_item = await make_template(session)
    _, plist = await make_trip(session)
    pi = await make_packing_item(session, plist.id, template_item_id=tmpl_item.id, is_customised=True)
    await session.commit()

    tmpl_item.name = "Template says this"
    summary = await propagate_template_change(
        session, tmpl.id,
        added_items=[], updated_items=[tmpl_item], removed_item_ids=[], today=TODAY,
    )

    await session.refresh(pi)
    assert pi.name == "Prop Item"  # unchanged
    assert summary["items_skipped_customised"] == 1
    assert summary["items_updated"] == 0


async def test_never_resets_is_packed(session):
    tmpl, tmpl_item = await make_template(session)
    _, plist = await make_trip(session)
    pi = await make_packing_item(session, plist.id, template_item_id=tmpl_item.id, is_packed=True)
    await session.commit()

    tmpl_item.name = "Renamed"
    await propagate_template_change(
        session, tmpl.id,
        added_items=[], updated_items=[tmpl_item], removed_item_ids=[], today=TODAY,
    )

    await session.refresh(pi)
    assert pi.is_packed is True  # never touched


async def test_removes_non_customised_item(session):
    tmpl, tmpl_item = await make_template(session)
    _, plist = await make_trip(session)
    pi = await make_packing_item(session, plist.id, template_item_id=tmpl_item.id)
    await session.commit()

    summary = await propagate_template_change(
        session, tmpl.id,
        added_items=[], updated_items=[], removed_item_ids=[tmpl_item.id], today=TODAY,
    )

    result = await session.execute(select(PackingItem).where(PackingItem.id == pi.id))
    assert result.scalar_one_or_none() is None
    assert summary["items_removed"] == 1


async def test_skips_customised_item_on_remove(session):
    tmpl, tmpl_item = await make_template(session)
    _, plist = await make_trip(session)
    pi = await make_packing_item(session, plist.id, template_item_id=tmpl_item.id, is_customised=True)
    await session.commit()

    summary = await propagate_template_change(
        session, tmpl.id,
        added_items=[], updated_items=[], removed_item_ids=[tmpl_item.id], today=TODAY,
    )

    result = await session.execute(select(PackingItem).where(PackingItem.id == pi.id))
    assert result.scalar_one_or_none() is not None  # still present
    assert summary["items_skipped_customised"] == 1
    assert summary["items_removed"] == 0


async def test_only_affects_active_trips_not_past(session):
    tmpl, tmpl_item = await make_template(session)
    _, past_list = await make_trip(session, end_date=PAST)
    await session.commit()

    summary = await propagate_template_change(
        session, tmpl.id,
        added_items=[tmpl_item], updated_items=[], removed_item_ids=[], today=TODAY,
    )

    result = await session.execute(select(PackingItem).where(PackingItem.list_id == past_list.id))
    assert result.scalars().all() == []
    assert summary["trips_updated"] == 0


async def test_only_affects_trips_with_matching_activity(session):
    tmpl, tmpl_item = await make_template(session, slug="test_act")
    _, other_list = await make_trip(session, slug="other_act")  # different activity
    await session.commit()

    summary = await propagate_template_change(
        session, tmpl.id,
        added_items=[tmpl_item], updated_items=[], removed_item_ids=[], today=TODAY,
    )

    result = await session.execute(select(PackingItem).where(PackingItem.list_id == other_list.id))
    assert result.scalars().all() == []
    assert summary["trips_updated"] == 0


async def test_summary_counts_are_correct(session):
    tmpl, tmpl_item = await make_template(session)
    _, plist = await make_trip(session)
    linked = await make_packing_item(session, plist.id, template_item_id=tmpl_item.id)
    await session.commit()

    new_item = ActivityTemplateItem(
        activity_template_id=tmpl.id, name="Brand new",
        quantity=1, is_essential=False, priority=3,
    )
    session.add(new_item)
    await session.flush()

    summary = await propagate_template_change(
        session, tmpl.id,
        added_items=[new_item],
        updated_items=[],
        removed_item_ids=[tmpl_item.id],
        today=TODAY,
    )

    assert summary["trips_updated"] == 1
    assert summary["items_added"] == 1
    assert summary["items_removed"] == 1
