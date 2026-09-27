from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class MenuBase(BaseModel):
    day_of_week: int = Field(
        ge=1,
        le=7,
        description=(
            "1=Monday, 2=Tuesday, "
            "3=Wednesday, 4=Thursday, "
            "5=Friday, 6=Saturday, 7=Sunday"
        ),
    )

    meal_slot_id: int = Field(gt=0)

    menu_items: list[str] = Field(
        min_length=1,
    )

    is_active: bool = True

    @field_validator("menu_items")
    @classmethod
    def validate_menu_items(
        cls,
        value: list[str],
    ) -> list[str]:
        cleaned_items = []

        for item in value:
            cleaned_item = item.strip()

            if cleaned_item:
                cleaned_items.append(cleaned_item)

        if not cleaned_items:
            raise ValueError(
                "At least one menu item is required"
            )

        # Duplicate items remove karein,
        # lekin original order preserve rahe.
        return list(dict.fromkeys(cleaned_items))


class MenuCreate(MenuBase):
    pass


class MenuUpdate(BaseModel):
    day_of_week: int | None = Field(
        default=None,
        ge=1,
        le=7,
    )

    meal_slot_id: int | None = Field(
        default=None,
        gt=0,
    )

    menu_items: list[str] | None = None

    is_active: bool | None = None

    @field_validator("menu_items")
    @classmethod
    def validate_menu_items(
        cls,
        value: list[str] | None,
    ) -> list[str] | None:
        if value is None:
            return None

        cleaned_items = [
            item.strip()
            for item in value
            if item.strip()
        ]

        if not cleaned_items:
            raise ValueError(
                "At least one menu item is required"
            )

        return list(dict.fromkeys(cleaned_items))


class MenuResponse(MenuBase):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    message: str