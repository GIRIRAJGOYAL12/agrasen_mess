from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.common.enums import UserRole
from src.database.dependencies import get_db
from src.modules.attendance import service
from src.modules.attendance.schema import (
    AdminMonthlyAttendanceResponse,
    AttendanceHistoryResponse,
    AttendanceScanResponse,
    MonthlyAttendanceResponse,
    QRScanRequest,
)
from src.modules.auth.dependencies import require_roles
from src.modules.users.model import User


router = APIRouter(
    prefix="/attendance",
    tags=["Attendance"],
)

DatabaseSession = Annotated[
    Session,
    Depends(get_db),
]

StudentUser = Annotated[
    User,
    Depends(require_roles(UserRole.STUDENT)),
]

ScannerUser = Annotated[
    User,
    Depends(
        require_roles(
            UserRole.STAFF,
            UserRole.ADMIN,
        )
    ),
]


@router.post(
    "/scan",
    response_model=AttendanceScanResponse,
)
def scan_student_qr(
    scan_data: QRScanRequest,
    db: DatabaseSession,
    scanner: ScannerUser,
):
    return service.scan_qr_and_record_attendance(
        db,
        scan_data.token,
        scanner,
    )


@router.get(
    "/me",
    response_model=MonthlyAttendanceResponse,
)
def get_my_attendance(
    db: DatabaseSession,
    current_student: StudentUser,
    year: Annotated[int, Query(ge=2000, le=2100)],
    month: Annotated[int, Query(ge=1, le=12)],
):
    return service.get_student_history(
        db,
        current_student,
        year,
        month,
    )

@router.get(
    "/summary",
    response_model=AdminMonthlyAttendanceResponse,
)
def get_admin_attendance_summary(
    db: DatabaseSession,
    staff_or_admin: ScannerUser,
    year: Annotated[
        int,
        Query(ge=2000, le=2100),
    ],
    month: Annotated[
        int,
        Query(ge=1, le=12),
    ],
):
    return service.get_admin_monthly_summary(
        db=db,
        year=year,
        month=month,
    )


@router.get(
    "",
    response_model=list[AttendanceHistoryResponse],
)
def get_attendance_report(
    db: DatabaseSession,
    staff_or_admin: ScannerUser,
    student_id: Annotated[
        int | None,
        Query(gt=0),
    ] = None,
    meal_slot_id: Annotated[
        int | None,
        Query(gt=0),
    ] = None,
    attendance_date: date | None = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return service.get_attendance_report(
        db=db,
        student_id=student_id,
        meal_slot_id=meal_slot_id,
        attendance_date=attendance_date,
        skip=skip,
        limit=limit,
    )