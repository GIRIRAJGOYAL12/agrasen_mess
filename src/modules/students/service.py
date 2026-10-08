from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.common.enums import UserRole
from src.core.security import hash_password
from src.modules.students import repository
from src.modules.students.model import Student
from src.modules.students.schema import StudentCreate, StudentUpdate
from src.modules.users import repository as user_repository
from src.modules.users.model import User


def create_student(
    db: Session,
    student_data: StudentCreate,
) -> Student:
    normalized_email = str(student_data.email).strip().lower()
    

    existing_user = user_repository.get_user_by_email(
        db,
        normalized_email,
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
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
    "email or phone number already exists"
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

def update_student(
    db: Session,
    student_id: int,
    student_data: StudentUpdate,
) -> Student:

    student = get_student(db, student_id)

    update_data = student_data.model_dump(
        exclude_unset=True
    )

    for field in ("name", "email", "room_number"):
        if field in update_data and update_data[field] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"{field} cannot be null",
            )

    if "name" in update_data:
        student.user.name = update_data["name"]

    if "email" in update_data:
        new_email = str(
            update_data["email"]
        ).strip().lower()

        existing_user = user_repository.get_user_by_email(
            db,
            new_email,
        )

        if (
            existing_user is not None
            and existing_user.id != student.user_id
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists",
            )

        student.user.email = new_email

    if "phone_number" in update_data:
        new_phone = update_data["phone_number"]

        if new_phone:
            existing_phone = user_repository.get_user_by_phone(
                db,
                new_phone,
            )

            if (
                existing_phone is not None
                and existing_phone.id != student.user_id
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Mobile number already exists",
                )

        student.user.phone_number = new_phone

    if "room_number" in update_data:
        student.room_number = update_data["room_number"]

    try:
        db.commit()

    except IntegrityError as error:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or mobile number already exists",
        ) from error

    return get_student(db, student_id)