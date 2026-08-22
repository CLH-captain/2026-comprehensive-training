from datetime import UTC, datetime, timedelta

import jwt
from fastapi.testclient import TestClient

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_argon2_password_round_trip() -> None:
    encoded = hash_password("safe-password")
    assert encoded.startswith("$argon2")
    assert verify_password("safe-password", encoded)
    assert not verify_password("wrong-password", encoded)


def test_access_token_round_trip() -> None:
    token, expected = create_access_token(
        user_id=42, role="admin", secret="x" * 32, expire_minutes=10
    )
    actual = decode_access_token(token, "x" * 32)
    assert actual.user_id == 42
    assert actual.role == "admin"
    assert actual.jti == expected.jti


def login(client: TestClient) -> str:
    response = client.post(
        "/api/auth/login",
        json={"username": "phase5_admin", "password": "Correct-Password-5"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_login_me_and_logout_revokes_token(auth_client: TestClient) -> None:
    token = login(auth_client)
    headers = {"Authorization": f"Bearer {token}"}
    me = auth_client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["role"] == "admin"

    logout = auth_client.post("/api/auth/logout", headers=headers)
    assert logout.status_code == 204
    rejected = auth_client.get("/api/auth/me", headers=headers)
    assert rejected.status_code == 401
    assert rejected.json()["code"] == "INVALID_TOKEN"


def test_bad_credentials_and_disabled_account_share_safe_error(
    auth_client: TestClient,
) -> None:
    for username, password in (
        ("phase5_admin", "wrong"),
        ("phase5_disabled", "Correct-Password-5"),
    ):
        response = auth_client.post(
            "/api/auth/login", json={"username": username, "password": password}
        )
        assert response.status_code == 401
        assert response.json()["code"] == "INVALID_CREDENTIALS"
        assert response.headers["X-Request-ID"] == response.json()["request_id"]


def test_missing_and_expired_tokens_return_uniform_error(auth_client: TestClient) -> None:
    missing = auth_client.get("/api/auth/me")
    assert missing.status_code == 401
    assert missing.json()["code"] == "AUTH_REQUIRED"

    now = datetime.now(UTC)
    expired = jwt.encode(
        {
            "sub": "1",
            "role": "admin",
            "jti": "expired-jti",
            "iat": now - timedelta(hours=2),
            "exp": now - timedelta(hours=1),
        },
        "phase5-test-secret-that-is-long-enough",
        algorithm="HS256",
    )
    response = auth_client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {expired}"}
    )
    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_TOKEN"
