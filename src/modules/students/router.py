from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from src.common.enums import UserRole
from src.database.dependencies import get_db
from src.modules.auth.dependencies import require_roles
from src.modules.students import service
from src.modules.students.schema import (
    StudentCreate,
    StudentUpdate,
    StudentResponse,
)
from src.modules.users.model import User
from src.modules.users.schema import AccountStatusUpdate

router = APIRouter(
    prefix="/students",
    tags=["Students"],
)

DatabaseSession = Annotated[
    Session,
    Depends(get_db),
]

AdminUser = Annotated[
    User,
    Depends(require_roles(UserRole.ADMIN)),
]


@router.post(
    "",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_student(
    student_data: StudentCreate,
    db: DatabaseSession,
    admin_user: AdminUser,
):
    return service.create_student(
        db,
        student_data,
    )


@router.get(
    "",
    response_model=list[StudentResponse],
)
def get_students(
    db: DatabaseSession,
    admin_user: AdminUser,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
):
    return service.list_students(
        db,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{student_id}",
    response_model=StudentResponse,
)
def get_student(
    student_id: int,
    db: DatabaseSession,
    admin_user: AdminUser,
):
    return service.get_student(
        db,
        student_id,
    )

@router.patch(
    "/{student_id}/status",
    response_model=StudentResponse,
)
def update_student_status(
    student_id: int,
    payload: AccountStatusUpdate,
    db: DatabaseSession,
    admin_user: AdminUser,
):
    return service.update_student_status(
        db,
        student_id,
        payload.is_active,
    )

@router.patch(
    "/{student_id}",
    response_model=StudentResponse,
)
def edit_student_details(
    student_id: int,
    payload: StudentUpdate,
    db: DatabaseSession,
    admin_user: AdminUser,
):
    return service.update_student(
        db,
        student_id,
        payload,
    )