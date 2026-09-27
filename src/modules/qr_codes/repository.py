from datetime import date, datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from src.modules.qr_codes.model import QRToken


def get_token_by_hash(
    db: Session,
    token_hash: str,
) -> QRToken | None:
    statement = select(QRToken).where(
        QRToken.token_hash == token_hash
    )

    return db.scalar(statement)


def remove_previous_unused_tokens(
    db: Session,
    student_id: int,
    meal_slot_id: int,
    meal_date: date,
) -> None:
    statement = delete(QRToken).where(
        QRToken.student_id == student_id,
        QRToken.meal_slot_id == meal_slot_id,
        QRToken.meal_date == meal_date,
        QRToken.used_at.is_(None),
    )

    db.execute(statement)


def create_qr_token(
    db: Session,
    student_id: int,
    meal_slot_id: int,
    meal_date: date,
    token_hash: str,
    expires_at: datetime,
) -> QRToken:
    qr_token = QRToken(
        student_id=student_id,
        meal_slot_id=meal_slot_id,
        meal_date=meal_date,
        token_hash=token_hash,
        expires_at=expires_at,
    )

    db.add(qr_token)
    db.commit()
    db.refresh(qr_token)

    return qr_token

def get_token_for_update(
    db: Session,
    token_hash: str,
) -> QRToken | None:
    statement = (
        select(QRToken)
        .where(QRToken.token_hash == token_hash)
        .with_for_update()
    )

    return db.scalar(statement)