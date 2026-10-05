from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.orm import Session

from src.modules.students.model import Student
from src.modules.users.model import User


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

def count_active_students(
    db: Session,
) -> int:
    statement = (
        select(
            func.count(Student.id)
        )
        .join(
            User,
            User.id == Student.user_id,
        )
        .where(
            User.is_active.is_(True),
        )
    )

    return int(
        db.scalar(statement) or 0
    )