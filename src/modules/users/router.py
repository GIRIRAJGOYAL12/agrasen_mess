from typing import Annotated


from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.common.enums import UserRole
from src.database.dependencies import get_db
from src.modules.auth.dependencies import require_roles
from src.modules.users import service
from src.modules.users.schema import (
    AccountStatusUpdate,
    StaffCreate,
    StaffUpdate,
    UserResponse,
)
from fastapi import APIRouter, Depends, HTTPException, status
from src.modules.users.model import User
from src.modules.users.schema import (
    StaffCreate,
    UserResponse,
)


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

DatabaseSession = Annotated[
    Session,
    Depends(get_db),
]

AdminUser = Annotated[
    User,
    Depends(require_roles(UserRole.ADMIN)),
]
class AccountStatusUpdate(BaseModel):
    is_active: bool

@router.post(
    "/staff",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_staff(
    staff_data: StaffCreate,
    db: DatabaseSession,
    admin_user: AdminUser,
):
    return service.create_staff(
        db,
        staff_data,
    )


@router.get(
    "/staff",
    response_model=list[UserResponse],
)
def get_staff_members(
    db: DatabaseSession,
    admin_user: AdminUser,
):
    return service.list_staff(db)

@router.patch(
    "/staff/{user_id}/status",
    response_model=UserResponse,
)
def update_staff_status(
    user_id: int,
    payload: AccountStatusUpdate,
    db: DatabaseSession,
    admin_user: AdminUser,
):
    staff_user = db.get(User, user_id)

    if staff_user is None or staff_user.role != UserRole.STAFF:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff member not found",
        )

    staff_user.is_active = payload.is_active
    db.commit()
    db.refresh(staff_user)

    return staff_user

@router.patch(
    "/staff/{user_id}",
    response_model=UserResponse,
)
def edit_staff_details(
    user_id: int,
    payload: StaffUpdate,
    db: DatabaseSession,
    admin_user: AdminUser,
):
    return service.update_staff(
        db,
        user_id,
        payload,
    )
