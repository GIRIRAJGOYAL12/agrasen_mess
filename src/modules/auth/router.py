from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database.dependencies import get_db
from src.modules.auth.dependencies import CurrentUser
from src.modules.auth.schema import (
    LoginRequest,
    LoginResponse,
)
from src.modules.auth.service import login_user
from src.modules.users.schema import UserResponse


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

DatabaseSession = Annotated[
    Session,
    Depends(get_db),
]


@router.post(
    "/login",
    response_model=LoginResponse,
)
def login(
    login_data: LoginRequest,
    db: DatabaseSession,
):
    return login_user(db, login_data)


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_logged_in_user(
    current_user: CurrentUser,
):
    return current_user