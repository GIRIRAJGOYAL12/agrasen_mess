from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.common.enums import UserRole
from src.database.dependencies import get_db
from src.modules.auth.dependencies import require_roles
from src.modules.qr_codes import service
from src.modules.qr_codes.schema import (
    QRGenerateRequest,
    QRGenerateResponse,
)
from src.modules.users.model import User


router = APIRouter(
    prefix="/qr-codes",
    tags=["QR Codes"],
)

DatabaseSession = Annotated[
    Session,
    Depends(get_db),
]

StudentUser = Annotated[
    User,
    Depends(require_roles(UserRole.STUDENT)),
]


@router.post(
    "/generate",
    response_model=QRGenerateResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_qr_code(
    request_data: QRGenerateRequest,
    db: DatabaseSession,
    current_student: StudentUser,
):
    return service.generate_qr_token(
        db,
        current_student,
        request_data,
    )