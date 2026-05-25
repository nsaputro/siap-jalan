from __future__ import annotations

import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ha_user_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    destination: Mapped[str] = mapped_column(String, nullable=False)
    country: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    start_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    end_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    duration_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    trip_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    activities: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    climate_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    traveller_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    packing_lists: Mapped[list[PackingList]] = relationship(
        "PackingList",
        back_populates="trip",
        cascade="all, delete-orphan",
    )


class PackingList(Base):
    __tablename__ = "packing_lists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    trip_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    trip: Mapped[Trip] = relationship("Trip", back_populates="packing_lists")
    items: Mapped[list[PackingItem]] = relationship(
        "PackingItem",
        back_populates="packing_list",
        cascade="all, delete-orphan",
    )


class PackingItem(Base):
    __tablename__ = "packing_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    list_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("packing_lists.id", ondelete="CASCADE"), nullable=False
    )
    # category kept for backward compat with existing DBs (NOT NULL constraint);
    # hidden from API schemas — all new items use the silent default "Other".
    category: Mapped[str] = mapped_column(String, nullable=False, default="Other")
    name: Mapped[str] = mapped_column(String, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_packed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_essential: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    added_by: Mapped[str] = mapped_column(String, default="user", nullable=False)
    source_activities: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    template_item_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("activity_template_items.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_customised: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    weight_grams: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bag_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    packing_list: Mapped[PackingList] = relationship(
        "PackingList", back_populates="items"
    )
    template_item: Mapped[Optional[ActivityTemplateItem]] = relationship(
        "ActivityTemplateItem", back_populates="packing_items"
    )


class ActivityTemplate(Base):
    __tablename__ = "activity_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    icon_emoji: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ha_user_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    climate_types: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    items: Mapped[list[ActivityTemplateItem]] = relationship(
        "ActivityTemplateItem",
        back_populates="activity_template",
        cascade="all, delete-orphan",
    )


class ActivityTemplateItem(Base):
    __tablename__ = "activity_template_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    activity_template_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("activity_templates.id", ondelete="CASCADE"),
        nullable=False,
    )
    # category kept for backward compat; hidden from API schemas.
    category: Mapped[str] = mapped_column(String, nullable=False, default="Other")
    name: Mapped[str] = mapped_column(String, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_essential: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    gender_filter: Mapped[str] = mapped_column(String, default="all", nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    activity_template: Mapped[ActivityTemplate] = relationship(
        "ActivityTemplate", back_populates="items"
    )
    packing_items: Mapped[list[PackingItem]] = relationship(
        "PackingItem", back_populates="template_item"
    )


class UserTripTemplate(Base):
    __tablename__ = "user_trip_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ha_user_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    activities: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    trip_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    climate_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    duration_min_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration_max_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    template_items: Mapped[list[UserTripTemplateItem]] = relationship(
        "UserTripTemplateItem",
        back_populates="template",
        cascade="all, delete-orphan",
    )


class UserTripTemplateItem(Base):
    __tablename__ = "user_trip_template_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    template_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user_trip_templates.id", ondelete="CASCADE"),
        nullable=False,
    )
    # category kept for backward compat; hidden from API schemas.
    category: Mapped[str] = mapped_column(String, nullable=False, default="Other")
    name: Mapped[str] = mapped_column(String, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_essential: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    template: Mapped[UserTripTemplate] = relationship(
        "UserTripTemplate", back_populates="template_items"
    )
