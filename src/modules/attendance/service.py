import calendar
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.common.enums import EntryMethod, MealType
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
    year: int,
    month: int,
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

    records = repository.get_student_monthly_attendance(
        db,
        student_id=student.id,
        year=year,
        month=month,
    )

    meal_slots = meal_repository.get_meals(
        db,
        active_only=False,
    )

    meal_slot_by_type = {
        meal.meal_type: meal
        for meal in meal_slots
    }

    attendance_by_day_and_type = {}

    for record in records:
        attendance_by_day_and_type[
            (
                record.meal_date,
                record.meal_slot.meal_type,
            )
        ] = record

    local_now = datetime.now(
        ZoneInfo(settings.app_timezone)
    )

    today = local_now.date()

    total_days = calendar.monthrange(
        year,
        month,
    )[1]

    summary = {
        "breakfast": 0,
        "lunch": 0,
        "dinner": 0,
    }

    days = []

    meal_types = [
        MealType.BREAKFAST,
        MealType.LUNCH,
        MealType.DINNER,
    ]

    for day_number in range(1, total_days + 1):
        current_date = date(
            year,
            month,
            day_number,
        )

        day_data = {
            "date": current_date,
        }

        for meal_type in meal_types:
            meal_key = meal_type.value

            meal_slot = meal_slot_by_type.get(
                meal_type
            )

            attendance = (
                attendance_by_day_and_type.get(
                    (
                        current_date,
                        meal_type,
                    )
                )
            )

            if attendance is not None:
                meal_status = "attended"
                attended_at = attendance.scanned_at

                summary[meal_key] += 1

            elif meal_slot is None or not meal_slot.is_active:
                meal_status = "unavailable"
                attended_at = None

            elif current_date > today:
                meal_status = "upcoming"
                attended_at = None

            elif current_date < today:
                meal_status = "missed"
                attended_at = None

            else:
                current_time = (
                    local_now.time().replace(
                        tzinfo=None
                    )
                )

                if current_time > meal_slot.end_time:
                    meal_status = "missed"
                else:
                    meal_status = "upcoming"

                attended_at = None

            day_data[meal_key] = {
                "status": meal_status,
                "attended_at": attended_at,
            }

        days.append(day_data)

    days.reverse()

    return {
        "year": year,
        "month": month,
        "total_days": total_days,
        "summary": summary,
        "days": days,
    }


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

def get_admin_monthly_summary(
    db: Session,
    year: int,
    month: int,
) -> dict:
    local_now = datetime.now(
        ZoneInfo(settings.app_timezone)
    )

    today = local_now.date()

    month_start = date(
        year,
        month,
        1,
    )

    last_day = calendar.monthrange(
        year,
        month,
    )[1]

    month_end = date(
        year,
        month,
        last_day,
    )

    # ---------------------------------------------------------
    # Do not calculate future attendance.
    # ---------------------------------------------------------

    if year == today.year and month == today.month:
        through_date = today

    elif (year, month) < (today.year, today.month):
        through_date = month_end

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Future month attendance is not available",
        )

    # ---------------------------------------------------------
    # TOTAL ACTIVE STUDENTS
    # ---------------------------------------------------------

    total_students = (
        student_repository.count_active_students(
            db
        )
    )

    # ---------------------------------------------------------
    # DAILY MEAL COUNTS
    # ---------------------------------------------------------

    daily_rows = (
        repository.get_daily_meal_counts(
            db,
            attendance_date=through_date,
        )
    )

    daily_counts = {
        "breakfast": 0,
        "lunch": 0,
        "dinner": 0,
    }

    for meal_type, count in daily_rows:
        daily_counts[
            meal_type.value
        ] = int(count)

    # ---------------------------------------------------------
    # MONTHLY MEAL COUNTS
    # ---------------------------------------------------------

    monthly_rows = (
        repository.get_monthly_meal_counts(
            db,
            start_date=month_start,
            end_date=through_date,
        )
    )

    monthly_counts = {
        "breakfast": 0,
        "lunch": 0,
        "dinner": 0,
    }

    for meal_type, count in monthly_rows:
        monthly_counts[
            meal_type.value
        ] = int(count)

    # ---------------------------------------------------------
    # DAILY COUPON COUNTS
    # ---------------------------------------------------------

    coupon_rows = (
        repository.get_daily_coupon_counts(
            db,
            start_date=month_start,
            end_date=through_date,
        )
    )

    coupon_by_date = {
        coupon_date: int(count)
        for coupon_date, count in coupon_rows
    }

    # Include zero-attendance dates as well.
    daily_coupon_counts = []

    current_date = month_start

    while current_date <= through_date:
        daily_coupon_counts.append(
            {
                "date": current_date,
                "count": coupon_by_date.get(
                    current_date,
                    0,
                ),
            }
        )

        current_date = date.fromordinal(
            current_date.toordinal() + 1
        )

    # ---------------------------------------------------------
    # MONTHLY COUPON TOTAL
    #
    # Each student contributes max 1 coupon per date.
    # ---------------------------------------------------------

    total_coupon_count = sum(
        item["count"]
        for item in daily_coupon_counts
    )

    daily_coupon_count = (
        coupon_by_date.get(
            through_date,
            0,
        )
    )

    # ---------------------------------------------------------
    # RESPONSE
    # ---------------------------------------------------------

    return {
        "year": year,
        "month": month,
        "through_date": through_date,

        "total_students": total_students,

        "daily_summary": {
            "date": through_date,
            "total_students": total_students,
            "breakfast": daily_counts[
                "breakfast"
            ],
            "lunch": daily_counts[
                "lunch"
            ],
            "dinner": daily_counts[
                "dinner"
            ],
            "coupon_count":
                daily_coupon_count,
        },

        "monthly_summary": {
            "breakfast": monthly_counts[
                "breakfast"
            ],
            "lunch": monthly_counts[
                "lunch"
            ],
            "dinner": monthly_counts[
                "dinner"
            ],
        },

        "total_coupon_count":
            total_coupon_count,

        "daily_coupon_counts":
            daily_coupon_counts,
    }