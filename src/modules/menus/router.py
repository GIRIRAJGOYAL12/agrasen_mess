from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Query,
    status,
)
from sqlalchemy.orm import Session

from src.common.enums import UserRole
from src.database.dependencies import get_db
from src.modules.auth.dependencies import (
    CurrentUser,
    require_roles,
)
from src.modules.menus import service
from src.modules.menus.schema import (
    MenuCreate,
    MenuResponse,
    MenuUpdate,
)
from src.modules.users.model import User


router = APIRouter(
    prefix="/menus",
    tags=["Menus"],
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
    response_model=MenuResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_menu(
    payload: MenuCreate,
    db: DatabaseSession,
    admin_user: AdminUser,
) -> MenuResponse:
    return service.create_menu(
        db=db,
        payload=payload,
    )


@router.get(
    "",
    response_model=list[MenuResponse],
)
def list_menus(
    db: DatabaseSession,
    current_user: CurrentUser,
    day_of_week: int | None = Query(
        default=None,
        ge=1,
        le=7,
    ),
    meal_slot_id: int | None = Query(
        default=None,
        gt=0,
    ),
    active_only: bool = False,
) -> list[MenuResponse]:
    return service.get_menus(
        db=db,
        day_of_week=day_of_week,
        meal_slot_id=meal_slot_id,
        active_only=active_only,
    )


@router.get(
    "/weekly",
    response_model=list[MenuResponse],
)
def get_weekly_menus(
    db: DatabaseSession,
    current_user: CurrentUser,
    active_only: bool = False,
) -> list[MenuResponse]:
    return service.get_weekly_menus(
        db=db,
        active_only=active_only,
    )


@router.get(
    "/today",
    response_model=list[MenuResponse],
)
def get_today_menus(
    db: DatabaseSession,
    current_user: CurrentUser,
) -> list[MenuResponse]:
    return service.get_today_menus(
        db=db,
    )


@router.get(
    "/{menu_id}",
    response_model=MenuResponse,
)
def get_menu(
    menu_id: int,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> MenuResponse:
    return service.get_menu_by_id(
        db=db,
        menu_id=menu_id,
    )


@router.patch(
    "/{menu_id}",
    response_model=MenuResponse,
)
def update_menu(
    menu_id: int,
    payload: MenuUpdate,
    db: DatabaseSession,
    admin_user: AdminUser,
) -> MenuResponse:
    return service.update_menu(
        db=db,
        menu_id=menu_id,
        payload=payload,
    )