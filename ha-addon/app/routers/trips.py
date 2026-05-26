from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..dependencies import get_ha_user
from ..models.packing import PackingItem, PackingList, Trip
from ..schemas.packing import TripCreate, TripResponse, TripUpdate
from ..services.activity_merger import merge_activities
from ..services.weather import get_weather

router = APIRouter(prefix="/trips", tags=["trips"])


@router.get("", response_model=list[TripResponse])
async def list_trips(
    db: AsyncSession = Depends(get_db),
    ha_user: str = Depends(get_ha_user),
):
    result = await db.execute(
        select(Trip)
        .where(Trip.ha_user_id == ha_user)
        .order_by(Trip.start_date.desc())
        .options(
            selectinload(Trip.packing_lists).selectinload(PackingList.items)
        )
    )
    return result.scalars().all()


@router.post("", response_model=TripResponse, status_code=201)
async def create_trip(
    body: TripCreate,
    db: AsyncSession = Depends(get_db),
    ha_user: str = Depends(get_ha_user),
):
    data = body.model_dump()
    # Auto-calculate duration_days if not provided
    if data.get("duration_days") is None:
        data["duration_days"] = (body.end_date - body.start_date).days

    trip = Trip(ha_user_id=ha_user, **data)
    db.add(trip)
    await db.flush()

    # Create default packing list
    default_list = PackingList(trip_id=trip.id, name="Main Packing List", is_default=True)
    db.add(default_list)
    await db.flush()

    # If activities specified, merge and bulk-insert items
    if body.activities:
        merged = await merge_activities(db, body.activities)
        for mi in merged:
            db.add(PackingItem(
                list_id=default_list.id,
                name=mi.name,
                quantity=mi.quantity,
                unit=mi.unit,
                is_essential=mi.is_essential,
                added_by="activity",
                source_activities=mi.source_activities,
                template_item_id=mi.template_item_id,
                is_customised=False,
            ))

    await db.commit()

    result = await db.execute(
        select(Trip)
        .where(Trip.id == trip.id)
        .options(selectinload(Trip.packing_lists).selectinload(PackingList.items))
    )
    return result.scalar_one()


@router.get("/{trip_id}", response_model=TripResponse)
async def get_trip(
    trip_id: int,
    db: AsyncSession = Depends(get_db),
    ha_user: str = Depends(get_ha_user),
):
    result = await db.execute(
        select(Trip)
        .where(Trip.id == trip_id, Trip.ha_user_id == ha_user)
        .options(selectinload(Trip.packing_lists).selectinload(PackingList.items))
    )
    trip = result.scalar_one_or_none()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


@router.put("/{trip_id}", response_model=TripResponse)
async def update_trip(
    trip_id: int,
    body: TripUpdate,
    db: AsyncSession = Depends(get_db),
    ha_user: str = Depends(get_ha_user),
):
    result = await db.execute(
        select(Trip)
        .where(Trip.id == trip_id, Trip.ha_user_id == ha_user)
        .options(selectinload(Trip.packing_lists).selectinload(PackingList.items))
    )
    trip = result.scalar_one_or_none()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    updates = body.model_dump(exclude_unset=True)

    # Track activity changes before applying
    old_slugs: set[str] = set(trip.activities or [])
    activities_changing = "activities" in updates

    # Recalculate duration_days when dates change
    if "start_date" in updates or "end_date" in updates:
        start = updates.get("start_date", trip.start_date)
        end = updates.get("end_date", trip.end_date)
        updates["duration_days"] = (end - start).days

    for field, value in updates.items():
        setattr(trip, field, value)

    # Propagate activity changes into the default packing list
    if activities_changing:
        new_slugs: set[str] = set(trip.activities or [])
        added = new_slugs - old_slugs
        removed = old_slugs - new_slugs

        default_list = next((pl for pl in trip.packing_lists if pl.is_default), None)
        if default_list and (added or removed):
            if added:
                merged = await merge_activities(db, list(added))
                existing_names = {pi.name.lower().strip() for pi in default_list.items}
                for mi in merged:
                    if mi.name.lower().strip() not in existing_names:
                        db.add(PackingItem(
                            list_id=default_list.id,
                            name=mi.name,
                            quantity=mi.quantity,
                            unit=mi.unit,
                            is_essential=mi.is_essential,
                            added_by="activity",
                            source_activities=mi.source_activities,
                            template_item_id=mi.template_item_id,
                            is_customised=False,
                        ))

            if removed:
                for item in list(default_list.items):
                    if item.is_customised:
                        continue
                    item_sources = set(item.source_activities or [])
                    # Only remove items that belong exclusively to removed activities
                    if item_sources and item_sources.issubset(removed):
                        await db.delete(item)

    await db.commit()

    result = await db.execute(
        select(Trip)
        .where(Trip.id == trip_id)
        .options(selectinload(Trip.packing_lists).selectinload(PackingList.items))
    )
    return result.scalar_one()


@router.delete("/{trip_id}", status_code=204)
async def delete_trip(
    trip_id: int,
    db: AsyncSession = Depends(get_db),
    ha_user: str = Depends(get_ha_user),
):
    result = await db.execute(
        select(Trip).where(Trip.id == trip_id, Trip.ha_user_id == ha_user)
    )
    trip = result.scalar_one_or_none()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    await db.delete(trip)
    await db.commit()


@router.get("/{trip_id}/weather")
async def trip_weather(
    trip_id: int,
    db: AsyncSession = Depends(get_db),
    ha_user: str = Depends(get_ha_user),
):
    result = await db.execute(
        select(Trip).where(Trip.id == trip_id, Trip.ha_user_id == ha_user)
    )
    trip = result.scalar_one_or_none()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    weather = await get_weather(trip.destination, trip.start_date, trip.end_date)
    if not weather:
        raise HTTPException(status_code=503, detail="Weather data unavailable")
    return weather
