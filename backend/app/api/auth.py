from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field

from app.api.dependencies import AuthenticatedUser
from app.core.errors import AppError
from app.core.security import create_access_token
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=200)


@router.post("/login")
def login(payload: LoginRequest, request: Request) -> dict:
    with request.app.state.engine.connect() as connection:
        user = AuthService(connection).authenticate(payload.username, payload.password)
    if user is None:
        raise AppError(401, "INVALID_CREDENTIALS", "Invalid username or password")
    token, claims = create_access_token(
        user_id=user["id"],
        role=user["role"],
        secret=request.app.state.settings.jwt_secret,
        expire_minutes=request.app.state.settings.jwt_expire_minutes,
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_at": claims.expires_at,
        "user": user,
    }


@router.get("/me")
def me(user: AuthenticatedUser) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "student_id": user.student_id,
    }


@router.post("/logout", status_code=204)
def logout(user: AuthenticatedUser, request: Request) -> None:
    with request.app.state.engine.begin() as connection:
        AuthService(connection).revoke(user_id=user.id, claims=user.token)
