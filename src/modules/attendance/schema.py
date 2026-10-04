from datetime import date, datetime

from pydantic import BaseModel, Field

from src.common.enums import EntryMethod, MealType


class QRScanRequest(BaseModel):
    token: str = Field(
        min_length=20,
        max_length=500,
    )


class AttendanceScanResponse(BaseModel):
    success: bool = True
    message: str

    attendance_id: int
    student_id: int
    student_name: str
    room_number: str
    photo_url: str | None  

    meal_slot_id: int
    meal_type: MealType
    meal_date: date

    scanned_at: datetime
    scanned_by: int
    entry_method: EntryMethod

class AttendanceHistoryResponse(BaseModel):
    id: int

    student_id: int
    student_name: str
    room_number: str

    meal_slot_id: int
    meal_type: MealType
    meal_date: date

    scanned_at: datetime
    scanner_name: str | None
    entry_method: EntryMethod


class MealAttendanceStatus(BaseModel):
    status: str
    attended_at: datetime | None = None


class DailyAttendanceResponse(BaseModel):
    date: date
    breakfast: MealAttendanceStatus
    lunch: MealAttendanceStatus
    dinner: MealAttendanceStatus


class MonthlyAttendanceSummary(BaseModel):
    breakfast: int
    lunch: int
    dinner: int


class MonthlyAttendanceResponse(BaseModel):
    year: int
    month: int
    total_days: int
    summary: MonthlyAttendanceSummary
    days: list[DailyAttendanceResponse]
