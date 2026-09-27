from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel

from src.common.enums import MealType


MealStatus = Literal[
    "completed",
    "available",
    "upcoming",
    "closed",
    "inactive",
]


class DashboardStudentProfile(BaseModel):
    student_id: int
    user_id: int
    name: str
    email: str
    roll_number: str
    hostel_name: str
    room_number: str
    course: str | None
    year: int | None
    photo_url: str | None


class DashboardMealStatus(BaseModel):
    meal_slot_id: int
    meal_type: MealType

    start_time: time
    end_time: time
    is_active: bool

    status: MealStatus
    can_generate_qr: bool

    attendance_recorded: bool
    attendance_id: int | None
    attended_at: datetime | None

    # menu_items: list[str]


class StudentDashboardResponse(BaseModel):
    date: date
    current_time: datetime
    timezone: str

    student: DashboardStudentProfile
    meals: list[DashboardMealStatus]

    completed_meals: int
    total_active_meals: int