from datetime import date

from sqlalchemy import extract, select
from sqlalchemy.orm import Session, selectinload

from src.modules.attendance.model import MealAttendance
from src.modules.students.model import Student


def get_student_meal_attendance(
    db: Session,
    student_id: int,
    meal_slot_id: int,
    meal_date: date,
) -> MealAttendance | None:
    statement = select(MealAttendance).where(
        MealAttendance.student_id == student_id,
        MealAttendance.meal_slot_id == meal_slot_id,
        MealAttendance.meal_date == meal_date,
    )

    return db.scalar(statement)


def get_attendance_by_id(
    db: Session,
    attendance_id: int,
) -> MealAttendance | None:
    statement = select(MealAttendance).where(
        MealAttendance.id == attendance_id
    )

    return db.scalar(statement)


def get_attendance_records(
    db: Session,
    student_id: int | None = None,
    meal_slot_id: int | None = None,
    attendance_date: date | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[MealAttendance]:
    statement = (
        select(MealAttendance)
        .options(
            selectinload(
                MealAttendance.student
            ).selectinload(Student.user),
            selectinload(
                MealAttendance.meal_slot
            ),
            selectinload(
                MealAttendance.scanner
            ),
        )
        .order_by(
            MealAttendance.scanned_at.desc()
        )
    )

    if student_id is not None:
        statement = statement.where(
            MealAttendance.student_id == student_id
        )

    if meal_slot_id is not None:
        statement = statement.where(
            MealAttendance.meal_slot_id
            == meal_slot_id
        )

    if attendance_date is not None:
        statement = statement.where(
            MealAttendance.meal_date
            == attendance_date
        )

    statement = statement.offset(skip).limit(limit)

    return list(db.scalars(statement).all())

def get_student_monthly_attendance(
    db: Session,
    student_id: int,
    year: int,
    month: int,
) -> list[MealAttendance]:
    statement = (
        select(MealAttendance)
        .options(
            selectinload(MealAttendance.meal_slot),
        )
        .where(
            MealAttendance.student_id == student_id,
            extract("year", MealAttendance.meal_date) == year,
            extract("month", MealAttendance.meal_date) == month,
        )
        .order_by(
            MealAttendance.meal_date.asc(),
            MealAttendance.scanned_at.asc(),
        )
    )

    return list(db.scalars(statement).all())