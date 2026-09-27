from sqlalchemy import select
from sqlalchemy.orm import Session

from src.common.enums import MealType
from src.modules.meals.model import MealSlot


def get_meal_by_id(
    db: Session,
    meal_id: int,
) -> MealSlot | None:
    statement = select(MealSlot).where(
        MealSlot.id == meal_id
    )

    return db.scalar(statement)


def get_meal_by_type(
    db: Session,
    meal_type: MealType,
) -> MealSlot | None:
    statement = select(MealSlot).where(
        MealSlot.meal_type == meal_type
    )

    return db.scalar(statement)


def get_meals(
    db: Session,
    active_only: bool = False,
) -> list[MealSlot]:
    statement = select(MealSlot)

    if active_only:
        statement = statement.where(
            MealSlot.is_active.is_(True)
        )

    statement = statement.order_by(
        MealSlot.start_time
    )

    return list(db.scalars(statement).all())