from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.modules.menus.model import Menu
from src.modules.menus.schema import (
    MenuCreate,
    MenuUpdate,
)


APP_TIMEZONE = ZoneInfo("Asia/Kolkata")


def get_menu_by_id(
    db: Session,
    menu_id: int,
) -> Menu:
    menu = db.scalar(
        select(Menu).where(
            Menu.id == menu_id,
        )
    )

    if menu is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu not found",
        )

    return menu


def get_menus(
    db: Session,
    day_of_week: int | None = None,
    meal_slot_id: int | None = None,
    active_only: bool = False,
) -> list[Menu]:
    statement = select(Menu)

    if day_of_week is not None:
        statement = statement.where(
            Menu.day_of_week == day_of_week,
        )

    if meal_slot_id is not None:
        statement = statement.where(
            Menu.meal_slot_id == meal_slot_id,
        )

    if active_only:
        statement = statement.where(
            Menu.is_active.is_(True),
        )

    statement = statement.order_by(
        Menu.day_of_week.asc(),
        Menu.meal_slot_id.asc(),
    )

    return list(
        db.scalars(statement).all()
    )


def get_weekly_menus(
    db: Session,
    active_only: bool = False,
) -> list[Menu]:
    return get_menus(
        db=db,
        active_only=active_only,
    )


def get_today_menus(
    db: Session,
) -> list[Menu]:
    current_day = datetime.now(
        APP_TIMEZONE
    ).isoweekday()

    return get_menus(
        db=db,
        day_of_week=current_day,
        active_only=True,
    )


def create_menu(
    db: Session,
    payload: MenuCreate,
) -> Menu:
    existing_menu = db.scalar(
        select(Menu).where(
            Menu.day_of_week ==
            payload.day_of_week,
            Menu.meal_slot_id ==
            payload.meal_slot_id,
        )
    )

    if existing_menu is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Menu already exists for this "
                "day and meal slot"
            ),
        )

    menu = Menu(
        day_of_week=payload.day_of_week,
        meal_slot_id=payload.meal_slot_id,
        menu_items=payload.menu_items,
        is_active=payload.is_active,
    )

    db.add(menu)

    try:
        db.commit()
        db.refresh(menu)
    except IntegrityError as error:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Invalid meal slot or duplicate menu"
            ),
        ) from error

    return menu


def update_menu(
    db: Session,
    menu_id: int,
    payload: MenuUpdate,
) -> Menu:
    menu = get_menu_by_id(
        db=db,
        menu_id=menu_id,
    )

    update_data = payload.model_dump(
        exclude_unset=True,
    )

    new_day = update_data.get(
        "day_of_week",
        menu.day_of_week,
    )

    new_meal_slot_id = update_data.get(
        "meal_slot_id",
        menu.meal_slot_id,
    )

    duplicate_menu = db.scalar(
        select(Menu).where(
            Menu.day_of_week == new_day,
            Menu.meal_slot_id ==
            new_meal_slot_id,
            Menu.id != menu.id,
        )
    )

    if duplicate_menu is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Another menu already exists for "
                "this day and meal slot"
            ),
        )

    for field, value in update_data.items():
        setattr(menu, field, value)

    try:
        db.commit()
        db.refresh(menu)
    except IntegrityError as error:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Menu update failed. Check meal slot."
            ),
        ) from error

    return menu