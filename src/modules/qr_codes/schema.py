from datetime import date, datetime

from pydantic import BaseModel, Field

from src.common.enums import MealType


class QRGenerateRequest(BaseModel):
    meal_slot_id: int = Field(gt=0)


class QRGenerateResponse(BaseModel):
    token: str
    token_type: str = "meal_qr"

    expires_at: datetime
    server_time: datetime
    expires_in: int

    student_id: int
    meal_slot_id: int
    meal_type: MealType
    meal_date: date