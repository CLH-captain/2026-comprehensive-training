from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
from pwdlib import PasswordHash

ALGORITHM = "HS256"
_password_hash = PasswordHash.recommended()


class InvalidTokenError(ValueError):
    pass


@dataclass(frozen=True)
class TokenClaims:
    user_id: int
    role: str
    jti: str
    issued_at: datetime
    expires_at: datetime


def hash_password(password: str) -> str:
    if not password:
        raise ValueError("Password must not be empty")
    return _password_hash.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _password_hash.verify(password, password_hash)
    except (ValueError, TypeError):
        return False


def create_access_token(
    *, user_id: int, role: str, secret: str, expire_minutes: int
) -> tuple[str, TokenClaims]:
    now = datetime.now(UTC)
    expires_at = now + timedelta(minutes=expire_minutes)
    claims = TokenClaims(
        user_id=user_id,
        role=role,
        jti=uuid4().hex,
        issued_at=now,
        expires_at=expires_at,
    )
    token = jwt.encode(
        {
            "sub": str(claims.user_id),
            "role": claims.role,
            "jti": claims.jti,
            "iat": claims.issued_at,
            "exp": claims.expires_at,
        },
        secret,
        algorithm=ALGORITHM,
    )
    return token, claims


def decode_access_token(token: str, secret: str) -> TokenClaims:
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=[ALGORITHM],
            options={"require": ["sub", "role", "jti", "iat", "exp"]},
        )
        user_id = int(payload["sub"])
        role = str(payload["role"])
        jti = str(payload["jti"])
        issued_at = datetime.fromtimestamp(int(payload["iat"]), UTC)
        expires_at = datetime.fromtimestamp(int(payload["exp"]), UTC)
    except (jwt.PyJWTError, KeyError, TypeError, ValueError) as exc:
        raise InvalidTokenError("Invalid or expired access token") from exc
    if user_id < 1 or not role or not jti:
        raise InvalidTokenError("Invalid access token claims")
    return TokenClaims(user_id, role, jti, issued_at, expires_at)
