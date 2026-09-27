from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.common.enums import UserRole
from src.database.dependencies import get_db
from src.modules.auth.dependencies import require_roles
from src.modules.dashboard import service
from src.modules.dashboard.schema import (
    StudentDashboardResponse,
)
from src.modules.users.model import User


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)

DatabaseSession = Annotated[
    Session,
    Depends(get_db),
]

StudentUser = Annotated[
    User,
    Depends(require_roles(UserRole.STUDENT)),
]


@router.get(
    "/student",
    response_model=StudentDashboardResponse,
)
def get_student_dashboard(
    db: DatabaseSession,
    current_student: StudentUser,
):
    return service.get_student_dashboard(
        db,
        current_student,
    )