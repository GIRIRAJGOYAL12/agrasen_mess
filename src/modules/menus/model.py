from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship


from src.database.base import Base


class Menu(Base):
    __tablename__ = "menus"

    __table_args__ = (
        UniqueConstraint(
            "day_of_week",
            "meal_slot_id",
            name="uq_menu_day_meal_slot",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    # ISO weekday:
    # 1=Monday, 2=Tuesday ... 7=Sunday
    day_of_week: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        index=True,
    )

    meal_slot_id: Mapped[int] = mapped_column(
        ForeignKey(
            "meal_slots.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    menu_items: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    meal_slot: Mapped["MealSlot"] = relationship(
    "MealSlot",
    back_populates="menus",
)