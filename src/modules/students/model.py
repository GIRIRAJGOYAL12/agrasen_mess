from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )

    roll_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )

    hostel_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    room_number: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    course: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    year: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    photo_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="student_profile",
    )

    qr_tokens = relationship(
        "QRToken",
        back_populates="student",
        cascade="all, delete-orphan",
    )

    attendance_records = relationship(
        "MealAttendance",
        back_populates="student",
        cascade="all, delete-orphan",
    )

    feedback_entries = relationship(
        "Feedback",
        back_populates="student",
        cascade="all, delete-orphan",
    )