from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.core.security import decode_access_token
from src.database.dependencies import get_db
from src.modules.users import repository as user_repository
from src.modules.users.model import User


bearer_scheme = HTTPBearer(
    auto_error=False,
)

DatabaseSession = Annotated[
    Session,
    Depends(get_db),
]


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    db: DatabaseSession,
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )

    if credentials is None:
        raise credentials_exception

    if credentials.scheme.lower() != "bearer":
        raise credentials_exception

    try:
        payload = decode_access_token(
            credentials.credentials
        )
        user_id = int(payload["sub"])
    except (ValueError, TypeError, KeyError):
        raise credentials_exception

    user = user_repository.get_user_by_id(
        db,
        user_id,
    )

    if user is None or not user.is_active:
        raise credentials_exception

    return user


CurrentUser = Annotated[
    User,
    Depends(get_current_user),
]

from collections.abc import Callable

from src.common.enums import UserRole


def require_roles(
    *allowed_roles: UserRole,
) -> Callable:
    def role_checker(
        current_user: CurrentUser,
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )

        return current_user

    return role_checker