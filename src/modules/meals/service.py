from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.modules.meals import repository
from src.modules.meals.model import MealSlot
from src.modules.meals.schema import (
    MealSlotCreate,
    MealSlotUpdate,
)


def create_meal(
    db: Session,
    meal_data: MealSlotCreate,
) -> MealSlot:
    existing_meal = repository.get_meal_by_type(
        db,
        meal_data.meal_type,
    )

    if existing_meal is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"{meal_data.meal_type.value.title()} "
                "meal slot already exists"
            ),
        )

    meal = MealSlot(
        meal_type=meal_data.meal_type,
        start_time=meal_data.start_time,
        end_time=meal_data.end_time,
        is_active=meal_data.is_active,
    )

    try:
        db.add(meal)
        db.commit()
        db.refresh(meal)
    except IntegrityError as error:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Meal slot already exists",
        ) from error

    return meal


def get_meal(
    db: Session,
    meal_id: int,
) -> MealSlot:
    meal = repository.get_meal_by_id(
        db,
        meal_id,
    )

    if meal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meal slot not found",
        )

    return meal


def list_meals(
    db: Session,
    active_only: bool,
) -> list[MealSlot]:
    return repository.get_meals(
        db,
        active_only=active_only,
    )


def update_meal(
    db: Session,
    meal_id: int,
    meal_data: MealSlotUpdate,
) -> MealSlot:
    meal = get_meal(db, meal_id)

    update_data = meal_data.model_dump(
        exclude_unset=True
    )

    new_start_time = update_data.get(
        "start_time",
        meal.start_time,
    )
    new_end_time = update_data.get(
        "end_time",
        meal.end_time,
    )

    if new_end_time <= new_start_time:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Meal end time must be after start time",
        )

    for field, value in update_data.items():
        setattr(meal, field, value)

    db.commit()
    db.refresh(meal)

    return meal