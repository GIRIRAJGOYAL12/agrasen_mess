from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.common.enums import UserRole
from src.core.security import hash_password
from src.modules.users import repository
from src.modules.users.model import User
from src.modules.users.schema import StaffCreate, StaffUpdate


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

def update_staff(
    db: Session,
    user_id: int,
    staff_data: StaffUpdate,
) -> User:

    staff = repository.get_user_by_id(db, user_id)

    if staff is None or staff.role != UserRole.STAFF:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff member not found",
        )

    update_data = staff_data.model_dump(
        exclude_unset=True
    )

    for field in ("name", "email"):
        if field in update_data and update_data[field] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"{field} cannot be null",
            )

    if "name" in update_data:
        staff.name = update_data["name"]

    if "email" in update_data:
        new_email = str(
            update_data["email"]
        ).strip().lower()

        existing_user = repository.get_user_by_email(
            db,
            new_email,
        )

        if (
            existing_user is not None
            and existing_user.id != staff.id
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists",
            )

        staff.email = new_email

    if "phone_number" in update_data:
        new_phone = update_data["phone_number"]

        if new_phone:
            existing_phone = repository.get_user_by_phone(
                db,
                new_phone,
            )

            if (
                existing_phone is not None
                and existing_phone.id != staff.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Mobile number already exists",
                )

        staff.phone_number = new_phone

    try:
        db.commit()

    except IntegrityError as error:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or mobile number already exists",
        ) from error

    db.refresh(staff)

    return staff