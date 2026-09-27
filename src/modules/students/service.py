from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.common.enums import UserRole
from src.core.security import hash_password
from src.modules.students import repository
from src.modules.students.model import Student
from src.modules.students.schema import StudentCreate
from src.modules.users import repository as user_repository
from src.modules.users.model import User


def create_student(
    db: Session,
    student_data: StudentCreate,
) -> Student:
    normalized_email = str(student_data.email).strip().lower()
    normalized_roll_number = (
        student_data.roll_number.strip().upper()
    )

    existing_user = user_repository.get_user_by_email(
        db,
        normalized_email,
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    existing_student = repository.get_student_by_roll_number(
        db,
        normalized_roll_number,
    )

    if existing_student is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A student with this roll number already exists",
        )

    user = User(
        name=student_data.name.strip(),
        email=normalized_email,
        phone_number=student_data.phone_number,
        password_hash=hash_password(
            student_data.password
        ),
        role=UserRole.STUDENT,
        is_active=True,
    )

    student = Student(
        user=user,
        roll_number=normalized_roll_number,
        hostel_name=student_data.hostel_name,
        room_number=student_data.room_number,
        course=student_data.course,
        year=student_data.year,
        photo_url=student_data.photo_url,
    )

    try:
        db.add(student)
        db.commit()
        db.refresh(student)
    except IntegrityError as error:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Student could not be created because "
                "email, phone number or roll number already exists"
            ),
        ) from error

    created_student = repository.get_student_by_id(
        db,
        student.id,
    )

    if created_student is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Student was created but could not be retrieved",
        )

    return created_student


def get_student(
    db: Session,
    student_id: int,
) -> Student:
    student = repository.get_student_by_id(
        db,
        student_id,
    )

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    return student


def list_students(
    db: Session,
    skip: int,
    limit: int,
) -> list[Student]:
    return repository.get_students(
        db,
        skip=skip,
        limit=limit,
    )

def update_student_status(
    db: Session,
    student_id: int,
    is_active: bool,
) -> Student:
    student = get_student(db, student_id)  # Existing 404 handling

    student.user.is_active = is_active
    db.commit()
    db.refresh(student)

    return get_student(db, student_id)