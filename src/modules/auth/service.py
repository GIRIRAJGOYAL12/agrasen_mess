from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import os
import smtplib
from email.message import EmailMessage

from src.core.config import settings
from src.core.security import (
    create_access_token,
    verify_password,
)
from src.modules.auth.schema import LoginRequest
from src.modules.users import repository as user_repository
from src.modules.users.model import User
from dotenv import load_dotenv

load_dotenv()


INVALID_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid email or password",
    headers={
        "WWW-Authenticate": "Bearer",
    },
)


def authenticate_user(
    db: Session,
    login_data: LoginRequest,
) -> User:
    user = user_repository.get_user_by_email(
        db,
        login_data.email,
    )

    if user is None:
        raise INVALID_CREDENTIALS

    if not verify_password(
        login_data.password,
        user.password_hash,
    ):
        raise INVALID_CREDENTIALS

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is inactive",
        )

    return user


def login_user(
    db: Session,
    login_data: LoginRequest,
) -> dict:
    user = authenticate_user(db, login_data)

    access_token = create_access_token(
        subject=str(user.id),
        additional_claims={
            "role": user.role.value,
        },
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": (
            settings.access_token_expire_minutes * 60
        ),
        "user": user,
    }

###################################################################

def send_reset_otp_email(to_email: str, otp: str) -> None:
    message = EmailMessage()

    message["Subject"] = "Hostel Mess - Password Reset OTP"
    message["From"] = os.environ["MAIL_FROM"]
    message["To"] = to_email

    message.set_content(
        "You requested a password reset for your Hostel Mess account.\n\n"
        f"Your OTP is: {otp}\n\n"
        "This OTP expires in 10 minutes. Do not share it with anyone.\n\n"
        "If you did not request this, you can ignore this email."
    )

    with smtplib.SMTP(
        host=os.environ["SMTP_HOST"],
        port=int(os.getenv("SMTP_PORT", "587")),
        timeout=15,
    ) as smtp:
        smtp.starttls()
        smtp.login(
            os.environ["SMTP_USERNAME"],
            os.environ["SMTP_PASSWORD"],
        )
        smtp.send_message(message)