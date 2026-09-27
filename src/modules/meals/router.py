from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from src.common.enums import UserRole
from src.database.dependencies import get_db
from src.modules.auth.dependencies import (
    CurrentUser,
    require_roles,
)
from src.modules.meals import service
from src.modules.meals.schema import (
    MealSlotCreate,
    MealSlotResponse,
    MealSlotUpdate,
)
from src.modules.users.model import User


router = APIRouter(
    prefix="/meals",
    tags=["Meals"],
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
    response_model=MealSlotResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_meal(
    meal_data: MealSlotCreate,
    db: DatabaseSession,
    admin_user: AdminUser,
):
    return service.create_meal(
        db,
        meal_data,
    )


@router.get(
    "",
    response_model=list[MealSlotResponse],
)
def get_meals(
    db: DatabaseSession,
    current_user: CurrentUser,
    active_only: Annotated[bool, Query()] = False,
):
    return service.list_meals(
        db,
        active_only=active_only,
    )


@router.get(
    "/{meal_id}",
    response_model=MealSlotResponse,
)
def get_meal(
    meal_id: int,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    return service.get_meal(
        db,
        meal_id,
    )


@router.patch(
    "/{meal_id}",
    response_model=MealSlotResponse,
)
def update_meal(
    meal_id: int,
    meal_data: MealSlotUpdate,
    db: DatabaseSession,
    admin_user: AdminUser,
):
    return service.update_meal(
        db,
        meal_id,
        meal_data,
    )