from datetime import time

from pydantic import BaseModel, ConfigDict, model_validator

from src.common.enums import MealType


class MealSlotCreate(BaseModel):
    meal_type: MealType
    start_time: time
    end_time: time
    is_active: bool = True

    @model_validator(mode="after")
    def validate_meal_time(self):
        if self.end_time <= self.start_time:
            raise ValueError(
                "Meal end time must be after start time"
            )

        return self


class MealSlotUpdate(BaseModel):
    start_time: time | None = None
    end_time: time | None = None
    is_active: bool | None = None


class MealSlotResponse(BaseModel):
    id: int
    meal_type: MealType
    start_time: time
    end_time: time
    is_active: bool

    model_config = ConfigDict(from_attributes=True)