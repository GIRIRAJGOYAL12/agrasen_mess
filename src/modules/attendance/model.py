from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.enums import EntryMethod
from src.database.base import Base


class MealAttendance(Base):
    __tablename__ = "meal_attendance"

    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "meal_slot_id",
            "meal_date",
            name="uq_student_meal_slot_date",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    meal_slot_id: Mapped[int] = mapped_column(
        ForeignKey("meal_slots.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )

    meal_date: Mapped[date] = mapped_column(
        Date,
        index=True,
        nullable=False,
    )

    scanned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    scanned_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    entry_method: Mapped[EntryMethod] = mapped_column(
        Enum(
            EntryMethod,
            name="entry_method",
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        default=EntryMethod.QR,
        nullable=False,
    )

    student = relationship(
        "Student",
        back_populates="attendance_records",
    )

    meal_slot = relationship(
        "MealSlot",
        back_populates="attendance_records",
    )

    scanner = relationship(
        "User",
        back_populates="scanned_attendance_records",
        foreign_keys=[scanned_by],
    )