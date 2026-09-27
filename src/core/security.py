from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from src.core.config import settings


password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    return password_hasher.verify(
        plain_password,
        hashed_password,
    )


def create_access_token(
    subject: str,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    payload: dict[str, Any] = {
        "sub": subject,
        "type": "access",
        "exp": expires_at,
        "iat": datetime.now(timezone.utc),
    }

    if additional_claims:
        payload.update(additional_claims)

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except InvalidTokenError as error:
        raise ValueError("Invalid or expired token") from error

    if payload.get("type") != "access":
        raise ValueError("Invalid token type")

    if not payload.get("sub"):
        raise ValueError("Token subject is missing")

    return payload