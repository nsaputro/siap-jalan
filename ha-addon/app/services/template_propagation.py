from __future__ import annotations

import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from ..models.packing import (
    ActivityTemplate,
    ActivityTemplateItem,
    PackingItem,
    PackingList,
    Trip,
)


async def propagate_template_change(
    db: AsyncSession,
    activity_template_id: int,
    added_items: list[Any],
    updated_items: list[Any],
    removed_item_ids: list[int],
    today: datetime.date,
) -> dict:
    # Fetch the template to get its slug
    tmpl_result = await db.execute(
        select(ActivityTemplate).where(ActivityTemplate.id == activity_template_id)
    )
    template = tmpl_result.scalar_one_or_none()
    if not template:
        return {
            "trips_updated": 0,
            "items_added": 0,
            "items_updated": 0,
            "items_removed": 0,
            "items_skipped_customised": 0,
        }

    slug = template.slug

    # Find active trips: end_date >= today AND activities contains slug
    trips_result = await db.execute(
        select(Trip)
        .where(Trip.end_date >= today)
        .options(
            selectinload(Trip.packing_lists).selectinload(PackingList.items)
        )
    )
    all_trips = trips_result.scalars().all()

    # Filter trips whose activities JSON contains the slug
    active_trips = [t for t in all_trips if slug in (t.activities or [])]

    trips_updated = 0
    items_added = 0
    items_updated = 0
    items_removed = 0
    items_skipped_customised = 0

    for trip in active_trips:
        # Find the default packing list
        default_list = next(
            (pl for pl in trip.packing_lists if pl.is_default), None
        )
        if not default_list:
            continue

        trip_modified = False

        # Build a map of normalised name -> item for quick lookup
        existing_by_name: dict[str, PackingItem] = {
            pi.name.lower().strip(): pi for pi in default_list.items
        }
        existing_by_template_id: dict[int, PackingItem] = {
            pi.template_item_id: pi
            for pi in default_list.items
            if pi.template_item_id is not None
        }

        # Process added items
        for new_item in added_items:
            norm_name = new_item.name.lower().strip()
            if norm_name not in existing_by_name:
                packing_item = PackingItem(
                    list_id=default_list.id,
                    category=new_item.category,
                    name=new_item.name,
                    quantity=new_item.quantity,
                    unit=new_item.unit if hasattr(new_item, "unit") else None,
                    is_essential=new_item.is_essential,
                    added_by="activity",
                    source_activities=[slug],
                    template_item_id=new_item.id,
                    is_customised=False,
                )
                db.add(packing_item)
                items_added += 1
                trip_modified = True

        # Process updated items
        for upd_item in updated_items:
            existing = existing_by_template_id.get(upd_item.id)
            if existing is None:
                continue
            if existing.is_customised:
                items_skipped_customised += 1
                continue
            existing.category = upd_item.category
            existing.name = upd_item.name
            existing.quantity = upd_item.quantity
            existing.unit = upd_item.unit if hasattr(upd_item, "unit") else existing.unit
            existing.is_essential = upd_item.is_essential
            items_updated += 1
            trip_modified = True

        # Process removed items
        for item in list(default_list.items):
            if item.template_item_id in removed_item_ids:
                if item.is_customised:
                    items_skipped_customised += 1
                    continue
                await db.delete(item)
                items_removed += 1
                trip_modified = True

        if trip_modified:
            trips_updated += 1

    await db.flush()

    return {
        "trips_updated": trips_updated,
        "items_added": items_added,
        "items_updated": items_updated,
        "items_removed": items_removed,
        "items_skipped_customised": items_skipped_customised,
    }
