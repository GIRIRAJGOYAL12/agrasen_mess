from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.common.enums import UserRole
from src.modules.users.model import User


def get_user_by_id(
    db: Session,
    user_id: int,
) -> User | None:
    statement = select(User).where(
        User.id == user_id
    )

    return db.scalar(statement)


def get_user_by_email(
    db: Session,
    email: str,
) -> User | None:
    normalized_email = email.strip().lower()

    statement = select(User).where(
        func.lower(User.email) == normalized_email
    )

    return db.scalar(statement)


def get_user_by_phone(
    db: Session,
    phone_number: str,
) -> User | None:
    statement = select(User).where(
        User.phone_number == phone_number
    )

    return db.scalar(statement)


def get_users_by_role(
    db: Session,
    role: UserRole,
) -> list[User]:
    statement = (
        select(User)
        .where(User.role == role)
        .order_by(User.id.desc())
    )

    return list(db.scalars(statement).all())


def add_user(
    db: Session,
    user: User,
) -> User:
    db.add(user)
    db.commit()
    db.refresh(user)

    return user