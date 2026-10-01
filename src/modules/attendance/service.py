from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.common.enums import EntryMethod
from src.core.config import settings
from src.modules.attendance import repository
from src.modules.attendance.model import MealAttendance
from src.modules.meals import repository as meal_repository
from src.modules.qr_codes import repository as qr_repository
from src.modules.qr_codes.utils import hash_qr_token
from src.modules.students import repository as student_repository
from src.modules.users.model import User


def scan_qr_and_record_attendance(
    db: Session,
    plain_token: str,
    scanner: User,
) -> dict:
    cleaned_token = plain_token.strip()

    token_hash = hash_qr_token(cleaned_token)

    qr_token = qr_repository.get_token_for_update(
        db,
        token_hash,
    )

    if qr_token is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid QR code",
        )

    now_utc = datetime.now(timezone.utc)

    if qr_token.used_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This QR code has already been used",
        )

    if qr_token.expires_at <= now_utc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="QR code has expired",
        )

    local_now = datetime.now(
        ZoneInfo(settings.app_timezone)
    )

    if qr_token.meal_date != local_now.date():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="QR code is not valid for today",
        )

    student = student_repository.get_student_by_id(
        db,
        qr_token.student_id,
    )

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found",
        )

    if not student.user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student account is inactive",
        )

    meal = meal_repository.get_meal_by_id(
        db,
        qr_token.meal_slot_id,
    )

    if meal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meal slot not found",
        )

    if not meal.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Meal slot is inactive",
        )

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
            detail="Current meal serving time has ended",
        )

    existing_attendance = (
        repository.get_student_meal_attendance(
            db,
            student_id=student.id,
            meal_slot_id=meal.id,
            meal_date=qr_token.meal_date,
        )
    )

    if existing_attendance is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"{meal.meal_type.value.title()} "
                "has already been recorded for this student"
            ),
        )

    attendance = MealAttendance(
        student_id=student.id,
        meal_slot_id=meal.id,
        meal_date=qr_token.meal_date,
        scanned_at=now_utc,
        scanned_by=scanner.id,
        entry_method=EntryMethod.QR,
    )

    qr_token.used_at = now_utc

    try:
        db.add(attendance)
        db.commit()
        db.refresh(attendance)
    except IntegrityError as error:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Meal attendance has already been recorded",
        ) from error

    return {
        "success": True,
        "message": (
            f"{meal.meal_type.value.title()} "
            "attendance recorded successfully"
        ),
        "attendance_id": attendance.id,
        "student_id": student.id,
        "student_name": student.user.name,
        "room_number": student.room_number,
        "photo_url": student.photo_url,
        "meal_slot_id": meal.id,
        "meal_type": meal.meal_type,
        "meal_date": attendance.meal_date,
        "scanned_at": attendance.scanned_at,
        "scanned_by": scanner.id,
        "entry_method": attendance.entry_method,
    }

def serialize_attendance(
    attendance: MealAttendance,
) -> dict:
    return {
        "id": attendance.id,
        "student_id": attendance.student_id,
        "student_name": attendance.student.user.name,
        "room_number": attendance.student.room_number,
        "meal_slot_id": attendance.meal_slot_id,
        "meal_type": attendance.meal_slot.meal_type,
        "meal_date": attendance.meal_date,
        "scanned_at": attendance.scanned_at,
        "scanner_name": (
            attendance.scanner.name
            if attendance.scanner
            else None
        ),
        "entry_method": attendance.entry_method,
    }


def get_student_history(
    db: Session,
    current_user: User,
    skip: int,
    limit: int,
) -> list[dict]:
    student = student_repository.get_student_by_user_id(
        db,
        current_user.id,
    )

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found",
        )

    records = repository.get_attendance_records(
        db,
        student_id=student.id,
        skip=skip,
        limit=limit,
    )

    return [
        serialize_attendance(record)
        for record in records
    ]


def get_attendance_report(
    db: Session,
    student_id: int | None,
    meal_slot_id: int | None,
    attendance_date,
    skip: int,
    limit: int,
) -> list[dict]:
    records = repository.get_attendance_records(
        db,
        student_id=student_id,
        meal_slot_id=meal_slot_id,
        attendance_date=attendance_date,
        skip=skip,
        limit=limit,
    )

    return [
        serialize_attendance(record)
        for record in records
    ]