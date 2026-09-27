from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import Base


class Feedback(Base):
    __tablename__ = "feedback"

    __table_args__ = (
        CheckConstraint(
            "rating >= 1 AND rating <= 5",
            name="ck_feedback_rating_range",
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

    rating: Mapped[int] = mapped_column(
        nullable=False,
    )

    comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    student = relationship(
        "Student",
        back_populates="feedback_entries",
    )