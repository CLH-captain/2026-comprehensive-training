from __future__ import annotations

from hmac import compare_digest
from typing import Annotated

from fastapi import Header, Request
from sqlalchemy import text

from app.core.errors import AppError
from app.core.permissions import AccessScope
from app.core.security import InvalidTokenError, decode_agent_context_token

AgentInternalKey = Annotated[str | None, Header(alias="X-Agent-Internal-Key")]
AgentContextToken = Annotated[str | None, Header(alias="X-Agent-Context-Token")]


def get_agent_scope(
    request: Request,
    internal_key: AgentInternalKey = None,
    context_token: AgentContextToken = None,
) -> AccessScope:
    settings = request.app.state.settings
    if not internal_key or not compare_digest(internal_key, settings.agent_internal_key):
        raise AppError(401, "INVALID_AGENT_KEY", "Invalid internal Agent credential")
    if not context_token:
        raise AppError(401, "AGENT_CONTEXT_REQUIRED", "Agent context token is required")
    try:
        claims = decode_agent_context_token(context_token, settings.jwt_secret)
    except InvalidTokenError as exc:
        raise AppError(401, "INVALID_AGENT_CONTEXT", str(exc)) from exc
    with request.app.state.engine.connect() as connection:
        user = connection.execute(
            text("SELECT id, role, student_id, status FROM users WHERE id = :id"),
            {"id": claims.user_id},
        ).mappings().one_or_none()
        if user is None or user["status"] != "active":
            raise AppError(401, "ACCOUNT_UNAVAILABLE", "Account is unavailable")
        club_ids = None
        if user["role"] != "admin":
            club_ids = (
                frozenset(
                    connection.scalars(
                        text(
                            "SELECT club_id FROM user_club_roles "
                            "WHERE user_id = :id AND role = 'manager'"
                        ),
                        {"id": claims.user_id},
                    ).all()
                )
                if user["role"] == "club_manager"
                else frozenset()
            )
    return AccessScope(user["id"], user["role"], user["student_id"], club_ids)