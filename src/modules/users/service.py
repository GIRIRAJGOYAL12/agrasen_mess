from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.common.enums import UserRole
from src.core.security import hash_password
from src.modules.users import repository
from src.modules.users.model import User
from src.modules.users.schema import StaffCreate


def create_staff(
    db: Session,
    staff_data: StaffCreate,
) -> User:
    normalized_email = str(
        staff_data.email
    ).strip().lower()

    existing_user = repository.get_user_by_email(
        db,
        normalized_email,
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    if staff_data.phone_number:
        existing_phone = repository.get_user_by_phone(
            db,
            staff_data.phone_number,
        )

        if existing_phone is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this phone number already exists",
            )

    staff = User(
        name=staff_data.name,
        email=normalized_email,
        phone_number=staff_data.phone_number,
        password_hash=hash_password(
            staff_data.password
        ),
        role=UserRole.STAFF,
        is_active=True,
    )

    try:
        return repository.add_user(db, staff)
    except IntegrityError as error:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Staff account already exists",
        ) from error


def list_staff(
    db: Session,
) -> list[User]:
    return repository.get_users_by_role(
        db,
        UserRole.STAFF,
    )