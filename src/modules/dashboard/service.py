from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.core.config import settings
from src.modules.attendance import repository as attendance_repository
from src.modules.meals import repository as meal_repository
# from src.modules.menus import repository as menu_repository
from src.modules.students import repository as student_repository
from src.modules.users.model import User


# def parse_menu_items(items: str) -> list[str]:
#     try:
#         parsed_items = json.loads(items)

#         if isinstance(parsed_items, list):
#             return [
#                 str(item)
#                 for item in parsed_items
#             ]
#     except (json.JSONDecodeError, TypeError):
#         pass

#     return [
#         item.strip()
#         for item in items.split(",")
#         if item.strip()
#     ]


def calculate_meal_status(
    is_active: bool,
    attendance_recorded: bool,
    start_time,
    end_time,
    current_time,
) -> str:
    if not is_active:
        return "inactive"

    if attendance_recorded:
        return "completed"

    if start_time <= current_time <= end_time:
        return "available"

    if current_time < start_time:
        return "upcoming"

    return "closed"


def get_student_dashboard(
    db: Session,
    current_user: User,
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

    local_now = datetime.now(
        ZoneInfo(settings.app_timezone)
    )

    current_date = local_now.date()
    current_time = local_now.time().replace(
        tzinfo=None
    )

    meals = meal_repository.get_meals(
        db,
        active_only=False,
    )

    # menus = menu_repository.get_menus_by_date(
    #     db,
    #     current_date,
    # )

    attendance_records = (
        attendance_repository.get_attendance_records(
            db,
            student_id=student.id,
            attendance_date=current_date,
            skip=0,
            limit=100,
        )
    )

    # menu_by_meal_slot = {
    #     menu.meal_slot_id: menu
    #     for menu in menus
    # }

    attendance_by_meal_slot = {
        record.meal_slot_id: record
        for record in attendance_records
    }

    dashboard_meals = []
    completed_meals = 0
    total_active_meals = 0

    for meal in meals:
        attendance = attendance_by_meal_slot.get(
            meal.id
        )
        # menu = menu_by_meal_slot.get(
        #     meal.id
        # )

        attendance_recorded = (
            attendance is not None
        )

        meal_status = calculate_meal_status(
            is_active=meal.is_active,
            attendance_recorded=attendance_recorded,
            start_time=meal.start_time,
            end_time=meal.end_time,
            current_time=current_time,
        )

        if meal.is_active:
            total_active_meals += 1

        if attendance_recorded:
            completed_meals += 1

        dashboard_meals.append(
            {
                "meal_slot_id": meal.id,
                "meal_type": meal.meal_type,
                "start_time": meal.start_time,
                "end_time": meal.end_time,
                "is_active": meal.is_active,
                "status": meal_status,
                "can_generate_qr": (
                    meal_status == "available"
                ),
                "attendance_recorded": (
                    attendance_recorded
                ),
                "attendance_id": (
                    attendance.id
                    if attendance
                    else None
                ),
                "attended_at": (
                    attendance.scanned_at
                    if attendance
                    else None
                ),
                # "menu_items": (
                #     parse_menu_items(menu.items)
                #     if menu
                #     else []
                # ),
            }
        )

    return {
        "date": current_date,
        "current_time": local_now,
        "timezone": settings.app_timezone,
        "student": {
            "student_id": student.id,
            "user_id": student.user_id,
            "name": student.user.name,
            "email": student.user.email,
            "room_number": student.room_number,
            "course": student.course,
            "year": student.year,
            "photo_url": student.photo_url,
        },
        "meals": dashboard_meals,
        "completed_meals": completed_meals,
        "total_active_meals": total_active_meals,
    }
