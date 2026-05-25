from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..dependencies import get_ha_user
from ..models.packing import PackingItem, PackingList, Trip, UserTripTemplate, UserTripTemplateItem
from ..schemas.packing import UserTripTemplateCreate, UserTripTemplateResponse

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("", response_model=list[UserTripTemplateResponse])
async def list_templates(
    db: AsyncSession = Depends(get_db),
    ha_user: str = Depends(get_ha_user),
):
    result = await db.execute(
        select(UserTripTemplate)
        .where(UserTripTemplate.ha_user_id == ha_user)
        .options(selectinload(UserTripTemplate.template_items))
    )
    return result.scalars().all()


@router.post("", response_model=UserTripTemplateResponse, status_code=201)
async def create_template(
    body: UserTripTemplateCreate,
    db: AsyncSession = Depends(get_db),
    ha_user: str = Depends(get_ha_user),
):
    tmpl = UserTripTemplate(
        ha_user_id=ha_user,
        name=body.name,
        description=body.description,
        activities=body.activities,
        trip_type=body.trip_type,
        climate_type=body.climate_type,
        duration_min_days=body.duration_min_days,
        duration_max_days=body.duration_max_days,
    )
    db.add(tmpl)
    await db.flush()

    for item_data in body.items:
        item = UserTripTemplateItem(
            template_id=tmpl.id,
            **item_data.model_dump(),
        )
        db.add(item)

    await db.commit()
    await db.refresh(tmpl)

    result = await db.execute(
        select(UserTripTemplate)
        .where(UserTripTemplate.id == tmpl.id)
        .options(selectinload(UserTripTemplate.template_items))
    )
    return result.scalar_one()


@router.get("/{template_id}", response_model=UserTripTemplateResponse)
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    ha_user: str = Depends(get_ha_user),
):
    result = await db.execute(
        select(UserTripTemplate)
        .where(
            UserTripTemplate.id == template_id,
            UserTripTemplate.ha_user_id == ha_user,
        )
        .options(selectinload(UserTripTemplate.template_items))
    )
    tmpl = result.scalar_one_or_none()
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")
    return tmpl


@router.delete("/{template_id}", status_code=204)
async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    ha_user: str = Depends(get_ha_user),
):
    result = await db.execute(
        select(UserTripTemplate).where(
            UserTripTemplate.id == template_id,
            UserTripTemplate.ha_user_id == ha_user,
        )
    )
    tmpl = result.scalar_one_or_none()
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")
    await db.delete(tmpl)
    await db.commit()


@router.post("/{template_id}/apply/{trip_id}", status_code=200)
async def apply_template(
    template_id: int,
    trip_id: int,
    db: AsyncSession = Depends(get_db),
    ha_user: str = Depends(get_ha_user),
):
    result = await db.execute(
        select(UserTripTemplate)
        .where(
            UserTripTemplate.id == template_id,
            UserTripTemplate.ha_user_id == ha_user,
        )
        .options(selectinload(UserTripTemplate.template_items))
    )
    tmpl = result.scalar_one_or_none()
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")

    result = await db.execute(
        select(Trip).where(Trip.id == trip_id, Trip.ha_user_id == ha_user)
    )
    trip = result.scalar_one_or_none()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    result = await db.execute(
        select(PackingList)
        .where(PackingList.trip_id == trip_id, PackingList.is_default == True)
        .options(selectinload(PackingList.items))
    )
    default_list = result.scalar_one_or_none()
    if not default_list:
        raise HTTPException(status_code=404, detail="No default packing list for trip")

    existing_names = {item.name.lower().strip() for item in default_list.items}
    added = 0
    for ti in tmpl.template_items:
        if ti.name.lower().strip() not in existing_names:
            item = PackingItem(
                list_id=default_list.id,
                name=ti.name,
                quantity=ti.quantity,
                is_essential=ti.is_essential,
                added_by="user",
            )
            db.add(item)
            added += 1

    await db.commit()
    return {"items_added": added}
