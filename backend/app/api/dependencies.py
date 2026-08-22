from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text

from app.core.errors import AppError
from app.core.permissions import AccessScope, load_access_scope
from app.core.security import InvalidTokenError, TokenClaims, decode_access_token

bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    id: int
    username: str
    role: str
    student_id: int | None
    token: TokenClaims


def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError(401, "AUTH_REQUIRED", "Authentication required")
    try:
        claims = decode_access_token(
            credentials.credentials, request.app.state.settings.jwt_secret
        )
    except InvalidTokenError as exc:
        raise AppError(401, "INVALID_TOKEN", str(exc)) from exc
    with request.app.state.engine.connect() as connection:
        row = connection.execute(
            text(
                """
                SELECT id, username, role, student_id, status
                FROM users WHERE id = :user_id
                """
            ),
            {"user_id": claims.user_id},
        ).mappings().one_or_none()
        revoked = connection.scalar(
            text("SELECT COUNT(*) FROM revoked_tokens WHERE jti = :jti"),
            {"jti": claims.jti},
        )
    if row is None or row["status"] != "active":
        raise AppError(401, "ACCOUNT_UNAVAILABLE", "Account is unavailable")
    if row["role"] != claims.role or revoked:
        raise AppError(401, "INVALID_TOKEN", "Access token is no longer valid")
    return CurrentUser(
        id=row["id"],
        username=row["username"],
        role=row["role"],
        student_id=row["student_id"],
        token=claims,
    )


AuthenticatedUser = Annotated[CurrentUser, Depends(get_current_user)]


def get_access_scope(request: Request, user: AuthenticatedUser) -> AccessScope:
    with request.app.state.engine.connect() as connection:
        return load_access_scope(connection, user)


AuthorizedScope = Annotated[AccessScope, Depends(get_access_scope)]