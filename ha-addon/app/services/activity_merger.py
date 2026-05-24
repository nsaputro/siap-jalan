from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from ..models.packing import ActivityTemplate


@dataclass
class MergedItem:
    name: str
    category: str
    quantity: int
    unit: Optional[str]
    is_essential: bool
    source_activities: list[str]
    priority: int
    template_item_id: Optional[int]


async def merge_activities(
    db: AsyncSession, slugs: list[str]
) -> list[MergedItem]:
    if not slugs:
        return []

    result = await db.execute(
        select(ActivityTemplate)
        .where(ActivityTemplate.slug.in_(slugs))
        .options(selectinload(ActivityTemplate.items))
    )
    templates = result.scalars().all()

    # Build a map slug -> template for source tracking
    slug_map: dict[str, ActivityTemplate] = {t.slug: t for t in templates}

    # Collect all raw items with their source slug
    raw_items: list[tuple[str, object]] = []
    for slug in slugs:
        template = slug_map.get(slug)
        if template:
            for item in template.items:
                raw_items.append((slug, item))

    # Deduplicate by normalised name
    # key: normalised_name -> MergedItem
    merged: dict[str, MergedItem] = {}

    for slug, item in raw_items:
        key = item.name.lower().strip()
        if key not in merged:
            merged[key] = MergedItem(
                name=item.name,
                category=item.category,
                quantity=item.quantity,
                unit=item.unit,
                is_essential=item.is_essential,
                source_activities=[slug],
                priority=item.priority,
                template_item_id=item.id,
            )
        else:
            existing = merged[key]
            # Accumulate source activities
            if slug not in existing.source_activities:
                existing.source_activities.append(slug)
            # is_essential = True if any source marks it essential
            if item.is_essential:
                existing.is_essential = True
            # quantity = max across sources
            if item.quantity > existing.quantity:
                existing.quantity = item.quantity
            # Winner for priority = highest priority; ties -> first found
            if item.priority > existing.priority:
                existing.priority = item.priority
                existing.template_item_id = item.id
                existing.name = item.name  # keep winner's name casing
                existing.category = item.category
                existing.unit = item.unit

    result_list = sorted(
        merged.values(), key=lambda x: (x.category, x.name)
    )
    return result_list
