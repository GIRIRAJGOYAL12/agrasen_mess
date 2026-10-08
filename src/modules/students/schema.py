from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)

from src.modules.users.schema import UserResponse


class StudentCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100,
    )

    email: EmailStr

    phone_number: str | None = Field(
        default=None,
        max_length=20,
    )

    password: str = Field(
        min_length=8,
        max_length=12,
    )

    room_number: str = Field(
        min_length=1,
        max_length=20,
    )

    course: str | None = Field(
        default=None,
        max_length=100,
    )

    year: int | None = Field(
        default=None,
        ge=1,
        le=8,
    )

    photo_url: str | None = None

    @field_validator("name", "room_number")
    @classmethod
    def strip_required_strings(cls, value: str) -> str:
        return value.strip()

    @field_validator("phone_number", "course", "photo_url")
    @classmethod
    def strip_optional_strings(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        stripped_value = value.strip()
        return stripped_value or None
class StudentUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    email: EmailStr | None = None

    phone_number: str | None = Field(
        default=None,
        max_length=20,
    )

    room_number: str | None = Field(
        default=None,
        min_length=1,
        max_length=20,
    )

    @field_validator("name", "room_number")
    @classmethod
    def clean_required_fields(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError("Field cannot be empty")

        return value

    @field_validator("phone_number")
    @classmethod
    def clean_phone_number(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            return None

        if not value.isdigit() or len(value) != 10:
            raise ValueError(
                "Mobile number must contain exactly 10 digits"
            )

        return value

class StudentResponse(BaseModel):
    id: int
    user_id: int
    room_number: str
    course: str | None
    year: int | None
    photo_url: str | None
    created_at: datetime
    user: UserResponse

    model_config = ConfigDict(from_attributes=True)