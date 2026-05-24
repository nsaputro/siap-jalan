from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..dependencies import get_ha_user
from ..models.packing import PackingItem, PackingList, Trip
from ..services.ai_suggestions import generate_suggestions
from ..services.weather import get_weather

router = APIRouter(tags=["ai"])


@router.post("/trips/{trip_id}/suggest")
async def suggest_items(
    trip_id: int,
    db: AsyncSession = Depends(get_db),
    ha_user: str = Depends(get_ha_user),
):
    result = await db.execute(
        select(Trip)
        .where(Trip.id == trip_id, Trip.ha_user_id == ha_user)
        .options(
            selectinload(Trip.packing_lists).selectinload(PackingList.items)
        )
    )
    trip = result.scalar_one_or_none()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Gather existing item names to avoid duplicates
    existing_names: list[str] = []
    default_list = None
    for plist in trip.packing_lists:
        if plist.is_default:
            default_list = plist
        for item in plist.items:
            existing_names.append(item.name)

    if not default_list:
        raise HTTPException(status_code=404, detail="No default packing list found")

    weather = await get_weather(trip.destination, trip.start_date, trip.end_date)

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    suggestions = await generate_suggestions(trip, weather, existing_names, api_key)

    if not suggestions:
        return {"added": 0, "items": []}

    existing_set = {n.lower().strip() for n in existing_names}
    new_items = []
    for suggestion in suggestions:
        name = suggestion.get("name", "")
        if name.lower().strip() in existing_set:
            continue
        item = PackingItem(
            list_id=default_list.id,
            category=suggestion.get("category", "Lainnya"),
            name=name,
            quantity=suggestion.get("quantity", 1),
            is_essential=suggestion.get("is_essential", False),
            added_by="ai",
            source_activities=[],
        )
        db.add(item)
        new_items.append(item)
        existing_set.add(name.lower().strip())

    await db.commit()
    for item in new_items:
        await db.refresh(item)

    return {"added": len(new_items), "items": new_items}
