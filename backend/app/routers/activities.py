from __future__ import annotations

import datetime
import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..dependencies import get_ha_user
from ..models.packing import ActivityTemplate, ActivityTemplateItem
from ..schemas.packing import (
    ActivityTemplateClone,
    ActivityTemplateCreate,
    ActivityTemplateItemCreate,
    ActivityTemplateItemResponse,
    ActivityTemplateItemUpdate,
    ActivityTemplateResponse,
    ActivityTemplateUpdate,
    MergeActivitiesRequest,
    MergedItemResponse,
)
from ..services.activity_merger import merge_activities
from ..services.template_propagation import propagate_template_change

router = APIRouter(prefix="/activities", tags=["activities"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_slug(name: str) -> str:
    """Convert a display name to a URL-safe slug."""
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return slug or "custom"


async def _unique_slug(db: AsyncSession, base: str) -> str:
    """Return *base* if unused, otherwise *base_2*, *base_3*, …"""
    candidate = base
    counter = 2
    while True:
        result = await db.execute(
            select(ActivityTemplate).where(ActivityTemplate.slug == candidate)
        )
        if result.scalar_one_or_none() is None:
            return candidate
        candidate = f"{base}_{counter}"
        counter += 1


def _assert_user_owns(tmpl: ActivityTemplate, ha_user: str) -> None:
    """Raise 403 if the template is built-in or belongs to a different user."""
    if tmpl.is_builtin:
        raise HTTPException(
            status_code=403,
            detail="Cannot modify a built-in activity template — clone it first.",
        )
    if tmpl.ha_user_id != ha_user:
        raise HTTPException(
            status_code=403,
            detail="You do not own this activity template.",
        )


async def _get_template(db: AsyncSession, template_id: int) -> ActivityTemplate:
    result = await db.execute(
        select(ActivityTemplate)
        .where(ActivityTemplate.id == template_id)
        .options(selectinload(ActivityTemplate.items))
    )
    tmpl = result.scalar_one_or_none()
    if not tmpl:
        raise HTTPException(status_code=404, detail="Activity template not found")
    return tmpl


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("", response_model=list[ActivityTemplateResponse])
async def list_activities(
    db: AsyncSession = Depends(get_db),
    ha_user: str = Depends(get_ha_user),
):
    result = await db.execute(
        select(ActivityTemplate)
        .where(
            (ActivityTemplate.is_builtin == True)
            | (ActivityTemplate.ha_user_id == ha_user)
        )
        .options(selectinload(ActivityTemplate.items))
    )
    return result.scalars().all()


@router.get("/{slug}", response_model=ActivityTemplateResponse)
async def get_activity(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ActivityTemplate)
        .where(ActivityTemplate.slug == slug)
        .options(selectinload(ActivityTemplate.items))
    )
    tmpl = result.scalar_one_or_none()
    if not tmpl:
        raise HTTPException(status_code=404, detail="Activity template not found")
    return tmpl


@router.post("", response_model=ActivityTemplateResponse, status_code=201)
async def create_activity(
    body: ActivityTemplateCreate,
    db: AsyncSession = Depends(get_db),
    ha_user: str = Depends(get_ha_user),
):
    base_slug = body.slug or _make_slug(body.name)
    slug = await _unique_slug(db, base_slug)

    tmpl = ActivityTemplate(
        slug=slug,
        name=body.name,
        icon_emoji=body.icon_emoji,
        description=body.description,
        climate_types=body.climate_types,
        is_builtin=False,
        ha_user_id=ha_user,
    )
    db.add(tmpl)
    await db.flush()

    for item_data in body.items:
        item = ActivityTemplateItem(
            activity_template_id=tmpl.id,
            **item_data.model_dump(),
        )
        db.add(item)

    await db.commit()
    await db.refresh(tmpl)

    result = await db.execute(
        select(ActivityTemplate)
        .where(ActivityTemplate.id == tmpl.id)
        .options(selectinload(ActivityTemplate.items))
    )
    return result.scalar_one()


@router.post("/{slug}/clone", response_model=ActivityTemplateResponse, status_code=201)
async def clone_activity(
    slug: str,
    body: ActivityTemplateClone,
    db: AsyncSession = Depends(get_db),
    ha_user: str = Depends(get_ha_user),
):
    # Fetch source template by slug (any template can be cloned)
    src_result = await db.execute(
        select(ActivityTemplate)
        .where(ActivityTemplate.slug == slug)
        .options(selectinload(ActivityTemplate.items))
    )
    source = src_result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Activity template not found")

    new_slug = await _unique_slug(db, _make_slug(body.name))

    clone = ActivityTemplate(
        slug=new_slug,
        name=body.name,
        icon_emoji=body.icon_emoji if body.icon_emoji is not None else source.icon_emoji,
        description=source.description,
        climate_types=list(source.climate_types),
        is_builtin=False,
        ha_user_id=ha_user,
    )
    db.add(clone)
    await db.flush()

    for src_item in source.items:
        db.add(ActivityTemplateItem(
            activity_template_id=clone.id,
            name=src_item.name,
            quantity=src_item.quantity,
            unit=src_item.unit,
            is_essential=src_item.is_essential,
            priority=src_item.priority,
            notes=src_item.notes,
            gender_filter=src_item.gender_filter,
        ))

    await db.commit()

    result = await db.execute(
        select(ActivityTemplate)
        .where(ActivityTemplate.id == clone.id)
        .options(selectinload(ActivityTemplate.items))
    )
    return result.scalar_one()


@router.put("/{template_id}", response_model=dict)
async def update_activity(
    template_id: int,
    body: ActivityTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    ha_user: str = Depends(get_ha_user),
):
    tmpl = await _get_template(db, template_id)
    _assert_user_owns(tmpl, ha_user)
    old_items = list(tmpl.items)

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(tmpl, field, value)

    await db.flush()
    today = datetime.date.today()
    summary = await propagate_template_change(
        db, template_id, [], old_items, [], today
    )
    await db.commit()
    await db.refresh(tmpl)

    result = await db.execute(
        select(ActivityTemplate)
        .where(ActivityTemplate.id == tmpl.id)
        .options(selectinload(ActivityTemplate.items))
    )
    refreshed = result.scalar_one()
    return {
        "template": ActivityTemplateResponse.model_validate(refreshed),
        "propagation_summary": summary,
    }


@router.delete("/{template_id}", status_code=204)
async def delete_activity(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    ha_user: str = Depends(get_ha_user),
):
    tmpl = await _get_template(db, template_id)
    _assert_user_owns(tmpl, ha_user)
    await db.delete(tmpl)
    await db.commit()


@router.post("/{template_id}/items", response_model=ActivityTemplateItemResponse, status_code=201)
async def add_template_item(
    template_id: int,
    body: ActivityTemplateItemCreate,
    db: AsyncSession = Depends(get_db),
    ha_user: str = Depends(get_ha_user),
):
    tmpl = await _get_template(db, template_id)
    _assert_user_owns(tmpl, ha_user)

    item = ActivityTemplateItem(
        activity_template_id=template_id,
        **body.model_dump(),
    )
    db.add(item)
    await db.flush()

    today = datetime.date.today()
    await propagate_template_change(db, template_id, [item], [], [], today)
    await db.commit()
    await db.refresh(item)
    return item


@router.put("/{template_id}/items/{item_id}", response_model=ActivityTemplateItemResponse)
async def update_template_item(
    template_id: int,
    item_id: int,
    body: ActivityTemplateItemUpdate,
    db: AsyncSession = Depends(get_db),
    ha_user: str = Depends(get_ha_user),
):
    tmpl = await _get_template(db, template_id)
    _assert_user_owns(tmpl, ha_user)

    result = await db.execute(
        select(ActivityTemplateItem).where(
            ActivityTemplateItem.id == item_id,
            ActivityTemplateItem.activity_template_id == template_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Template item not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(item, field, value)

    await db.flush()
    today = datetime.date.today()
    await propagate_template_change(db, template_id, [], [item], [], today)
    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/{template_id}/items/{item_id}", status_code=204)
async def delete_template_item(
    template_id: int,
    item_id: int,
    db: AsyncSession = Depends(get_db),
    ha_user: str = Depends(get_ha_user),
):
    tmpl = await _get_template(db, template_id)
    _assert_user_owns(tmpl, ha_user)

    result = await db.execute(
        select(ActivityTemplateItem).where(
            ActivityTemplateItem.id == item_id,
            ActivityTemplateItem.activity_template_id == template_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Template item not found")

    today = datetime.date.today()
    await propagate_template_change(db, template_id, [], [], [item_id], today)
    await db.delete(item)
    await db.commit()


@router.post("/merge", response_model=list[MergedItemResponse])
async def merge_activity_items(
    body: MergeActivitiesRequest,
    db: AsyncSession = Depends(get_db),
):
    merged = await merge_activities(db, body.activity_slugs)
    return [
        MergedItemResponse(
            name=mi.name,
            quantity=mi.quantity,
            unit=mi.unit,
            is_essential=mi.is_essential,
            source_activities=mi.source_activities,
            priority=mi.priority,
        )
        for mi in merged
    ]
