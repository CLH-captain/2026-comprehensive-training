import pytest
from app.core.security import (
    InvalidTokenError,
    create_agent_context_token,
    decode_agent_context_token,
)


def test_agent_context_token_round_trip() -> None:
    token = create_agent_context_token(
        user_id=42, conversation_id=9, secret="x" * 32
    )
    claims = decode_agent_context_token(token, "x" * 32)
    assert claims.user_id == 42
    assert claims.conversation_id == 9


def test_agent_context_token_rejects_wrong_secret() -> None:
    token = create_agent_context_token(
        user_id=42, conversation_id=None, secret="x" * 32
    )
    with pytest.raises(InvalidTokenError):
        decode_agent_context_token(token, "y" * 32)
