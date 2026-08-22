from __future__ import annotations

from datetime import UTC

from sqlalchemy import Connection, text

from app.core.security import TokenClaims, verify_password


class AuthService:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def authenticate(self, username: str, password: str) -> dict | None:
        user = self.connection.execute(
            text(
                """
                SELECT id, username, password_hash, role, student_id, status
                FROM users WHERE username = :username
                """
            ),
            {"username": username},
        ).mappings().one_or_none()
        if (
            user is None
            or user["status"] != "active"
            or not verify_password(password, user["password_hash"])
        ):
            return None
        return {key: value for key, value in user.items() if key != "password_hash"}

    def revoke(self, *, user_id: int, claims: TokenClaims) -> None:
        self.connection.execute(
            text(
                """
                INSERT INTO revoked_tokens (user_id, jti, expires_at, revoked_at)
                VALUES (:user_id, :jti, :expires_at, UTC_TIMESTAMP())
                ON DUPLICATE KEY UPDATE jti = VALUES(jti)
                """
            ),
            {
                "user_id": user_id,
                "jti": claims.jti,
                "expires_at": claims.expires_at.astimezone(UTC).replace(tzinfo=None),
            },
        )
