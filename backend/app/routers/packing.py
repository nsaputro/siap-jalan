from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models.packing import ActivityTemplate, PackingItem, PackingList, Trip
from ..schemas.packing import (
    PackingItemCreate,
    PackingItemResponse,
    PackingItemUpdate,
    PackingListCreate,
    PackingListResponse,
)

router = APIRouter(tags=["packing"])

HA_USER_ID = "default"

# ---------------------------------------------------------------------------
# Lists
# ---------------------------------------------------------------------------

@router.get("/trips/{trip_id}/lists", response_model=list[PackingListResponse])
async def list_packing_lists(
    trip_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Trip).where(Trip.id == trip_id, Trip.ha_user_id == HA_USER_ID)
    )
    trip = result.scalar_one_or_none()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    result = await db.execute(
        select(PackingList)
        .where(PackingList.trip_id == trip_id)
        .options(selectinload(PackingList.items))
    )
    return result.scalars().all()


@router.post("/trips/{trip_id}/lists", response_model=PackingListResponse, status_code=201)
async def create_packing_list(
    trip_id: int,
    body: PackingListCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Trip).where(Trip.id == trip_id, Trip.ha_user_id == HA_USER_ID)
    )
    trip = result.scalar_one_or_none()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    plist = PackingList(trip_id=trip_id, **body.model_dump())
    db.add(plist)
    await db.commit()
    await db.refresh(plist)

    result = await db.execute(
        select(PackingList)
        .where(PackingList.id == plist.id)
        .options(selectinload(PackingList.items))
    )
    return result.scalar_one()


# ---------------------------------------------------------------------------
# Items
# ---------------------------------------------------------------------------

@router.get("/lists/{list_id}/items", response_model=list[PackingItemResponse])
async def list_items(
    list_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PackingItem).where(PackingItem.list_id == list_id)
    )
    return result.scalars().all()


@router.post("/lists/{list_id}/items", response_model=PackingItemResponse, status_code=201)
async def create_item(
    list_id: int,
    body: PackingItemCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PackingList).where(PackingList.id == list_id)
    )
    plist = result.scalar_one_or_none()
    if not plist:
        raise HTTPException(status_code=404, detail="Packing list not found")

    data = body.model_dump(exclude={"source_activity"})
    if body.source_activity:
        data["added_by"] = "adhoc"

    item = PackingItem(list_id=list_id, **data)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.put("/items/{item_id}", response_model=PackingItemResponse)
async def update_item(
    item_id: int,
    body: PackingItemUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PackingItem).where(PackingItem.id == item_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    updates = body.model_dump(exclude_unset=True)

    # If item has a template and we're changing something other than is_packed/is_customised
    non_pack_fields = {k for k in updates if k not in ("is_packed", "is_customised")}
    if item.template_item_id is not None and non_pack_fields:
        item.is_customised = True

    for field, value in updates.items():
        setattr(item, field, value)

    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/items/{item_id}", status_code=204)
async def delete_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PackingItem).where(PackingItem.id == item_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    await db.delete(item)
    await db.commit()


@router.post("/items/{item_id}/toggle", response_model=PackingItemResponse)
async def toggle_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PackingItem).where(PackingItem.id == item_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    item.is_packed = not item.is_packed
    await db.commit()
    await db.refresh(item)
    return item


@router.post("/items/{item_id}/promote", response_model=PackingItemResponse)
async def promote_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Link item to an ActivityTemplateItem by matching name in source_activities[0] template."""
    result = await db.execute(
        select(PackingItem).where(PackingItem.id == item_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    source_activities = item.source_activities or []
    if not source_activities:
        raise HTTPException(status_code=400, detail="Item has no source activities")

    slug = source_activities[0]
    result = await db.execute(
        select(ActivityTemplate)
        .where(ActivityTemplate.slug == slug)
        .options(selectinload(ActivityTemplate.items))
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Activity template not found")

    norm_name = item.name.lower().strip()
    matched = next(
        (ti for ti in template.items if ti.name.lower().strip() == norm_name), None
    )
    if not matched:
        raise HTTPException(status_code=404, detail="No matching template item found")

    item.template_item_id = matched.id
    await db.commit()
    await db.refresh(item)
    return item


@router.post("/items/bulk", response_model=list[PackingItemResponse], status_code=201)
async def bulk_create_items(
    body: list[PackingItemCreate],
    db: AsyncSession = Depends(get_db),
):
    items = []
    for item_data in body:
        data = item_data.model_dump(exclude={"source_activity"})
        item = PackingItem(**data)
        db.add(item)
        items.append(item)
    await db.commit()
    for item in items:
        await db.refresh(item)
    return items
