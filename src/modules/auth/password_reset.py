import hashlib
import hmac
import logging
import os
import secrets
import smtplib
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from src.database.dependencies import get_db
from src.modules.auth.models.reset_password import PasswordResetOTP
from src.modules.auth.schema import (
    ForgotPasswordRequest,
    MessageResponse,
    ResetPasswordRequest,
)
from src.modules.auth.service import (
    send_reset_otp_email,
)

from src.modules.users.model import User  # TODO: apna User model import
from src.core.security import hash_password  # TODO: existing hashing function

load_dotenv()

router = APIRouter(prefix="/auth", tags=["Auth"])
logger = logging.getLogger(__name__)

FORGOT_MESSAGE = "If this email is registered, an OTP will be sent."
INVALID_OTP_MESSAGE = "Invalid or expired OTP."


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def make_otp_hash(user_id: int, otp: str) -> str:
    """
    6-digit OTP ko secret key ke saath HMAC hash karta hai.
    Sirf plain SHA-256 use karna suitable nahi hai:
    6-digit OTP ke saare combinations guess kiye ja sakte hain.
    """
    secret = os.environ["PASSWORD_RESET_SECRET"].encode("utf-8")
    value = f"{user_id}:{otp}".encode("utf-8")

    return hmac.new(
        secret,
        value,
        hashlib.sha256,
    ).hexdigest()


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
def forgot_password(
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    email = str(payload.email).strip().lower()
    now = utc_now()

    # Same response for registered and unregistered emails.
    user = db.scalar(
        select(User).where(User.email == email)
    )

    if user is None:
        return MessageResponse(message=FORGOT_MESSAGE)

    latest_otp = db.scalar(
        select(PasswordResetOTP)
        .where(PasswordResetOTP.user_id == user.id)
        .order_by(PasswordResetOTP.created_at.desc())
        .limit(1)
    )

    # 60-second resend cooldown.
    if latest_otp is not None:
        seconds_since_last_request = (
            now - latest_otp.created_at
        ).total_seconds()

        if seconds_since_last_request < 60:
            return MessageResponse(message=FORGOT_MESSAGE)

    otp = f"{secrets.randbelow(1_000_000):06d}"

    new_record = PasswordResetOTP(
        user_id=user.id,
        otp_hash=make_otp_hash(user.id, otp),
        attempts=0,
        created_at=now,
        expires_at=now + timedelta(minutes=10),
    )

    try:
        # Email fail hone par OTP database mein save nahi hoga.
        send_reset_otp_email(user.email, otp)

        # Purane unused OTP invalidate karo.
        db.execute(
            update(PasswordResetOTP)
            .where(
                PasswordResetOTP.user_id == user.id,
                PasswordResetOTP.used_at.is_(None),
            )
            .values(used_at=now)
        )

        db.add(new_record)
        db.commit()

    except (smtplib.SMTPException, OSError):
        db.rollback()
        logger.exception(
            "Password reset OTP email could not be sent for user_id=%s",
            user.id,
        )

        # SMTP problem aur unknown email se different public response mat do.
        return MessageResponse(message=FORGOT_MESSAGE)

    except Exception:
        db.rollback()
        logger.exception(
            "Could not save password reset OTP for user_id=%s",
            user.id,
        )
        raise

    return MessageResponse(message=FORGOT_MESSAGE)


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
def reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    email = str(payload.email).strip().lower()
    now = utc_now()

    user = db.scalar(
        select(User).where(User.email == email)
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=INVALID_OTP_MESSAGE,
        )

    # PostgreSQL row lock: ek OTP par simultaneous requests ko serialize karta hai.
    otp_record = db.scalar(
        select(PasswordResetOTP)
        .where(
            PasswordResetOTP.user_id == user.id,
            PasswordResetOTP.used_at.is_(None),
        )
        .order_by(PasswordResetOTP.created_at.desc())
        .limit(1)
        .with_for_update()
    )

    if otp_record is None or otp_record.expires_at <= now:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=INVALID_OTP_MESSAGE,
        )

    if otp_record.attempts >= 5:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Too many attempts. Request a new OTP.",
        )

    submitted_hash = make_otp_hash(user.id, payload.otp)

    if not hmac.compare_digest(
        otp_record.otp_hash,
        submitted_hash,
    ):
        otp_record.attempts += 1

        if otp_record.attempts >= 5:
            otp_record.used_at = now

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=INVALID_OTP_MESSAGE,
        )

    # IMPORTANT: login mein jo hashing function use hota hai, wahi yahan use karo.
    user.password_hash = hash_password(payload.new_password)
    otp_record.used_at = now

    # User ke baaki unused OTP bhi invalidate kar do.
    db.execute(
        update(PasswordResetOTP)
        .where(
            PasswordResetOTP.user_id == user.id,
            PasswordResetOTP.used_at.is_(None),
        )
        .values(used_at=now)
    )

    db.commit()

    return MessageResponse(
        message="Password updated successfully. Please log in."
    )