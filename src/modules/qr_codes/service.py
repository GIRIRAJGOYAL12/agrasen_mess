import secrets
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.core.config import settings
from src.modules.attendance import repository as attendance_repository
from src.modules.meals import repository as meal_repository
from src.modules.qr_codes import repository
from src.modules.qr_codes.schema import QRGenerateRequest
from src.modules.students import repository as student_repository
from src.modules.users.model import User
from src.modules.qr_codes.utils import hash_qr_token




def generate_qr_token(
    db: Session,
    current_user: User,
    request_data: QRGenerateRequest,
) -> dict:
    student = student_repository.get_student_by_user_id(
        db,
        current_user.id,
    )

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found",
        )

    meal = meal_repository.get_meal_by_id(
        db,
        request_data.meal_slot_id,
    )

    if meal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meal slot not found",
        )

    if not meal.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This meal slot is currently inactive",
        )

    local_timezone = ZoneInfo(
        settings.app_timezone
    )
    local_now = datetime.now(local_timezone)

    current_date = local_now.date()
    current_time = local_now.time().replace(
        tzinfo=None
    )

    if not (
        meal.start_time
        <= current_time
        <= meal.end_time
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"{meal.meal_type.value.title()} QR can only "
                f"be generated between "
                f"{meal.start_time.strftime('%H:%M')} and "
                f"{meal.end_time.strftime('%H:%M')}"
            ),
        )

    attendance = (
        attendance_repository.get_student_meal_attendance(
            db,
            student_id=student.id,
            meal_slot_id=meal.id,
            meal_date=current_date,
        )
    )

    if attendance is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"{meal.meal_type.value.title()} "
                "has already been recorded today"
            ),
        )

    plain_token = secrets.token_urlsafe(32)
    token_hash = hash_qr_token(plain_token)

    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(
            seconds=settings.qr_expiry_seconds
        )
    )

    repository.remove_previous_unused_tokens(
        db,
        student_id=student.id,
        meal_slot_id=meal.id,
        meal_date=current_date,
    )

    repository.create_qr_token(
        db,
        student_id=student.id,
        meal_slot_id=meal.id,
        meal_date=current_date,
        token_hash=token_hash,
        expires_at=expires_at,
    )

    return {
        "token": plain_token,
        "token_type": "meal_qr",
        "expires_at": expires_at,
        "expires_in": settings.qr_expiry_seconds,
        "student_id": student.id,
        "meal_slot_id": meal.id,
        "meal_type": meal.meal_type,
        "meal_date": current_date,
    }