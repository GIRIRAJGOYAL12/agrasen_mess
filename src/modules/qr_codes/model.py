from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import Base


class QRToken(Base):
    __tablename__ = "qr_tokens"

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

    token_hash: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    student = relationship(
        "Student",
        back_populates="qr_tokens",
    )

    meal_slot = relationship(
        "MealSlot",
        back_populates="qr_tokens",
    )