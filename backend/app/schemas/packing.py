from __future__ import annotations

import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, model_validator


# ---------------------------------------------------------------------------
# ActivityTemplateItem
# ---------------------------------------------------------------------------

class ActivityTemplateItemCreate(BaseModel):
    name: str
    quantity: int = 1
    unit: Optional[str] = None
    is_essential: bool = False
    priority: int = 0
    notes: Optional[str] = None
    gender_filter: str = "all"


class ActivityTemplateItemUpdate(BaseModel):
    name: Optional[str] = None
    quantity: Optional[int] = None
    unit: Optional[str] = None
    is_essential: Optional[bool] = None
    is_hidden: Optional[bool] = None
    priority: Optional[int] = None
    notes: Optional[str] = None
    gender_filter: Optional[str] = None


class ActivityTemplateItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    activity_template_id: int
    name: str
    quantity: int
    unit: Optional[str]
    is_essential: bool
    is_hidden: bool
    is_user_added: bool
    priority: int
    notes: Optional[str]
    gender_filter: str
    created_at: datetime.datetime


# ---------------------------------------------------------------------------
# ActivityTemplate
# ---------------------------------------------------------------------------

class ActivityTemplateCreate(BaseModel):
    slug: Optional[str] = None  # auto-generated from name when omitted
    name: str
    icon_emoji: str = "🎒"
    description: Optional[str] = None
    climate_types: list[str] = []
    items: list[ActivityTemplateItemCreate] = []


class ActivityTemplateClone(BaseModel):
    name: str
    icon_emoji: Optional[str] = None  # defaults to source template's emoji


class ActivityTemplateUpdate(BaseModel):
    name: Optional[str] = None
    icon_emoji: Optional[str] = None
    description: Optional[str] = None
    climate_types: Optional[list[str]] = None


class ActivityTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    icon_emoji: str
    description: Optional[str]
    is_builtin: bool
    ha_user_id: Optional[str]
    climate_types: list
    created_at: datetime.datetime
    updated_at: datetime.datetime
    items: list[ActivityTemplateItemResponse] = []


# ---------------------------------------------------------------------------
# PackingItem
# ---------------------------------------------------------------------------

class PackingItemCreate(BaseModel):
    name: str
    quantity: int = 1
    unit: Optional[str] = None
    is_essential: bool = False
    added_by: str = "user"
    source_activities: list[str] = []
    source_activity: Optional[str] = None  # convenience: appended to source_activities
    weight_grams: Optional[int] = None
    bag_type: Optional[str] = None

    @model_validator(mode="after")
    def append_source_activity(self) -> PackingItemCreate:
        if self.source_activity and self.source_activity not in self.source_activities:
            self.source_activities = list(self.source_activities) + [self.source_activity]
        return self


class PackingItemBulkCreate(PackingItemCreate):
    """PackingItemCreate extended with list_id for the bulk-create endpoint."""
    list_id: int


class PackingItemUpdate(BaseModel):
    name: Optional[str] = None
    quantity: Optional[int] = None
    unit: Optional[str] = None
    is_packed: Optional[bool] = None
    is_essential: Optional[bool] = None
    added_by: Optional[str] = None
    source_activities: Optional[list[str]] = None
    is_customised: Optional[bool] = None
    weight_grams: Optional[int] = None
    bag_type: Optional[str] = None


class PackingItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    list_id: int
    name: str
    quantity: int
    unit: Optional[str]
    is_packed: bool
    is_essential: bool
    added_by: str
    source_activities: list
    template_item_id: Optional[int]
    is_customised: bool
    weight_grams: Optional[int]
    bag_type: Optional[str]
    created_at: datetime.datetime
    updated_at: datetime.datetime


# ---------------------------------------------------------------------------
# PackingList
# ---------------------------------------------------------------------------

class PackingListCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_default: bool = True


class PackingListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    trip_id: int
    name: str
    description: Optional[str]
    is_default: bool
    created_at: datetime.datetime
    items: list[PackingItemResponse] = []


# ---------------------------------------------------------------------------
# Trip
# ---------------------------------------------------------------------------

class TripCreate(BaseModel):
    destination: str
    country: Optional[str] = None
    start_date: datetime.date
    end_date: datetime.date
    duration_days: Optional[int] = None
    trip_type: Optional[str] = None
    activities: list[str] = []
    climate_type: Optional[str] = None
    notes: Optional[str] = None
    traveller_count: int = 1


class TripUpdate(BaseModel):
    destination: Optional[str] = None
    country: Optional[str] = None
    start_date: Optional[datetime.date] = None
    end_date: Optional[datetime.date] = None
    duration_days: Optional[int] = None
    trip_type: Optional[str] = None
    activities: Optional[list[str]] = None
    climate_type: Optional[str] = None
    notes: Optional[str] = None
    traveller_count: Optional[int] = None


class TripResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ha_user_id: Optional[str]
    destination: str
    country: Optional[str]
    start_date: datetime.date
    end_date: datetime.date
    duration_days: Optional[int]
    trip_type: Optional[str]
    activities: list
    climate_type: Optional[str]
    notes: Optional[str]
    traveller_count: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    packing_lists: list[PackingListResponse] = []


# ---------------------------------------------------------------------------
# UserTripTemplate
# ---------------------------------------------------------------------------

class UserTripTemplateItemCreate(BaseModel):
    name: str
    quantity: int = 1
    is_essential: bool = False


class UserTripTemplateItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    template_id: int
    name: str
    quantity: int
    is_essential: bool


class UserTripTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    activities: list[str] = []
    trip_type: Optional[str] = None
    climate_type: Optional[str] = None
    duration_min_days: Optional[int] = None
    duration_max_days: Optional[int] = None
    items: list[UserTripTemplateItemCreate] = []


class UserTripTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ha_user_id: Optional[str]
    name: str
    description: Optional[str]
    activities: list
    trip_type: Optional[str]
    climate_type: Optional[str]
    duration_min_days: Optional[int]
    duration_max_days: Optional[int]
    created_at: datetime.datetime
    template_items: list[UserTripTemplateItemResponse] = []


# ---------------------------------------------------------------------------
# Merge / AI helpers
# ---------------------------------------------------------------------------

class MergeActivitiesRequest(BaseModel):
    activity_slugs: list[str]


class MergedItemResponse(BaseModel):
    name: str
    quantity: int
    unit: Optional[str]
    is_essential: bool
    source_activities: list[str]
    priority: int
