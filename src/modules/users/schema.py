from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from src.common.enums import UserRole

class AccountStatusUpdate(BaseModel):
    is_active: bool

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone_number: str | None
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StaffCreate(BaseModel):
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

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("phone_number")
    @classmethod
    def clean_phone_number(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip()
        return value or None

class StaffUpdate(BaseModel):
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

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if len(value) < 2:
            raise ValueError(
                "Name must contain at least 2 characters"
            )

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
    