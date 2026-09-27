from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from src.modules.students.model import Student


def get_student_by_id(
    db: Session,
    student_id: int,
) -> Student | None:
    statement = (
        select(Student)
        .options(selectinload(Student.user))
        .where(Student.id == student_id)
    )

    return db.scalar(statement)


def get_student_by_roll_number(
    db: Session,
    roll_number: str,
) -> Student | None:
    normalized_roll_number = roll_number.strip().upper()

    statement = select(Student).where(
        func.upper(Student.roll_number)
        == normalized_roll_number
    )

    return db.scalar(statement)


def get_students(
    db: Session,
    skip: int = 0,
    limit: int = 100,
) -> list[Student]:
    statement = (
        select(Student)
        .options(selectinload(Student.user))
        .order_by(Student.id.desc())
        .offset(skip)
        .limit(limit)
    )

    return list(db.scalars(statement).all())

def get_student_by_user_id(
    db: Session,
    user_id: int,
) -> Student | None:
    statement = (
        select(Student)
        .options(selectinload(Student.user))
        .where(Student.user_id == user_id)
    )

    return db.scalar(statement)