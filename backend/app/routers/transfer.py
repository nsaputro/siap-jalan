from __future__ import annotations

import datetime
import json

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models.packing import (
    ActivityTemplate,
    ActivityTemplateItem,
    PackingItem,
    PackingList,
    Trip,
)
from ..schemas.packing import ImportPayload, ImportResult

router = APIRouter(tags=["transfer"])

HA_USER_ID = "default"


@router.get("/export")
async def export_data(
    include_trips: bool = Query(True, alias="trips"),
    include_activities: bool = Query(True, alias="activities"),
    db: AsyncSession = Depends(get_db),
) -> Response:
    today = datetime.date.today()

    trips: list = []
    if include_trips:
        trips_result = await db.execute(
            select(Trip)
            .where(Trip.ha_user_id == HA_USER_ID, Trip.end_date >= today)
            .options(selectinload(Trip.packing_lists).selectinload(PackingList.items))
            .order_by(Trip.start_date)
        )
        trips = list(trips_result.scalars().all())

    activities: list = []
    if include_activities:
        acts_result = await db.execute(
            select(ActivityTemplate)
            .where(ActivityTemplate.ha_user_id == HA_USER_ID, ActivityTemplate.is_builtin.is_(False))
            .options(selectinload(ActivityTemplate.items))
            .order_by(ActivityTemplate.name)
        )
        activities = list(acts_result.scalars().all())

    payload = {
        "version": "1",
        "exported_at": datetime.datetime.utcnow().isoformat() + "Z",
        "trips": [
            {
                "destination": t.destination,
                "country": t.country,
                "start_date": t.start_date.isoformat(),
                "end_date": t.end_date.isoformat(),
                "duration_days": t.duration_days,
                "trip_type": t.trip_type,
                "activities": t.activities,
                "notes": t.notes,
                "traveller_count": t.traveller_count,
                "packing_lists": [
                    {
                        "name": pl.name,
                        "is_default": pl.is_default,
                        "items": [
                            {
                                "name": pi.name,
                                "quantity": pi.quantity,
                                "unit": pi.unit,
                                "is_packed": pi.is_packed,
                                "is_essential": pi.is_essential,
                                "added_by": pi.added_by,
                                "source_activities": pi.source_activities,
                                "is_customised": pi.is_customised,
                            }
                            for pi in pl.items
                        ],
                    }
                    for pl in t.packing_lists
                ],
            }
            for t in trips
        ],
        "activities": [
            {
                "slug": a.slug,
                "name": a.name,
                "icon_emoji": a.icon_emoji,
                "description": a.description,
                "climate_types": a.climate_types,
                "items": [
                    {
                        "name": i.name,
                        "quantity": i.quantity,
                        "unit": i.unit,
                        "is_essential": i.is_essential,
                        "priority": i.priority,
                        "notes": i.notes,
                        "gender_filter": i.gender_filter,
                        "is_hidden": i.is_hidden,
                        "is_user_added": i.is_user_added,
                    }
                    for i in a.items
                ],
            }
            for a in activities
        ],
    }

    filename = f"siapjalan-{today.isoformat()}.json"
    return Response(
        content=json.dumps(payload, ensure_ascii=False, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/import", response_model=ImportResult)
async def import_data(
    payload: ImportPayload,
    db: AsyncSession = Depends(get_db),
) -> ImportResult:
    warnings: list[str] = []
    slug_map: dict[str, str] = {}
    activities_imported = 0

    existing_slugs_result = await db.execute(select(ActivityTemplate.slug))
    used_slugs: set[str] = set(existing_slugs_result.scalars().all())

    for act in payload.activities:
        target = act.slug
        if target in used_slugs:
            i = 2
            while f"{act.slug}_{i}" in used_slugs:
                i += 1
            target = f"{act.slug}_{i}"
            warnings.append(
                f"Activity '{act.name}': slug '{act.slug}' already exists, imported as '{target}'"
            )

        if target != act.slug:
            slug_map[act.slug] = target
        used_slugs.add(target)

        tmpl = ActivityTemplate(
            slug=target,
            name=act.name,
            icon_emoji=act.icon_emoji,
            description=act.description,
            climate_types=act.climate_types,
            is_builtin=False,
            ha_user_id=HA_USER_ID,
        )
        db.add(tmpl)
        await db.flush()

        for item in act.items:
            db.add(ActivityTemplateItem(
                activity_template_id=tmpl.id,
                name=item.name,
                quantity=item.quantity,
                unit=item.unit,
                is_essential=item.is_essential,
                priority=item.priority,
                notes=item.notes,
                gender_filter=item.gender_filter,
                is_hidden=item.is_hidden,
                is_user_added=item.is_user_added,
            ))

        activities_imported += 1

    trips_imported = 0
    for trip_data in payload.trips:
        remapped = [slug_map.get(s, s) for s in trip_data.activities]
        duration = trip_data.duration_days or (trip_data.end_date - trip_data.start_date).days

        trip = Trip(
            ha_user_id=HA_USER_ID,
            destination=trip_data.destination,
            country=trip_data.country,
            start_date=trip_data.start_date,
            end_date=trip_data.end_date,
            duration_days=duration,
            trip_type=trip_data.trip_type,
            activities=remapped,
            notes=trip_data.notes,
            traveller_count=trip_data.traveller_count,
        )
        db.add(trip)
        await db.flush()

        for list_data in trip_data.packing_lists:
            plist = PackingList(
                trip_id=trip.id,
                name=list_data.name,
                is_default=list_data.is_default,
            )
            db.add(plist)
            await db.flush()

            for item in list_data.items:
                remapped_sources = [slug_map.get(s, s) for s in item.source_activities]
                db.add(PackingItem(
                    list_id=plist.id,
                    name=item.name,
                    quantity=item.quantity,
                    unit=item.unit,
                    is_packed=item.is_packed,
                    is_essential=item.is_essential,
                    added_by=item.added_by,
                    source_activities=remapped_sources,
                    is_customised=item.is_customised,
                ))

        trips_imported += 1

    await db.commit()
    return ImportResult(
        trips_imported=trips_imported,
        activities_imported=activities_imported,
        warnings=warnings,
    )
