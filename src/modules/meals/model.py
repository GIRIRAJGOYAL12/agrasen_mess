from datetime import datetime, time

from sqlalchemy import Boolean, DateTime, Enum, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.enums import MealType
from src.database.base import Base


class MealSlot(Base):
    __tablename__ = "meal_slots"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    meal_type: Mapped[MealType] = mapped_column(
        Enum(
            MealType,
            name="meal_type",
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        unique=True,
        nullable=False,
    )

    start_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    end_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    qr_tokens = relationship(
        "QRToken",
        back_populates="meal_slot",
    )

    attendance_records = relationship(
        "MealAttendance",
        back_populates="meal_slot",
    )

    menus = relationship(
        "Menu",
        back_populates="meal_slot",
        cascade="all, delete-orphan",
    )