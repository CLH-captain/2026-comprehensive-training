from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
from app.core.config import get_settings
from app.core.security import ALGORITHM, create_agent_context_token
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

INTERNAL_KEY = "phase5-agent-key-that-is-long-enough"
JWT_SECRET = "phase5-test-secret-that-is-long-enough"


def user_id(client: TestClient, username: str) -> int:
    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": "Correct-Password-5"},
    )
    assert response.status_code == 200
    return response.json()["user"]["id"]


def tool_headers(client: TestClient, username: str) -> dict[str, str]:
    token = create_agent_context_token(
        user_id=user_id(client, username),
        conversation_id=7,
        secret=JWT_SECRET,
    )
    return {
        "X-Agent-Internal-Key": INTERNAL_KEY,
        "X-Agent-Context-Token": token,
    }


def test_internal_tools_require_both_credentials(auth_client: TestClient) -> None:
    missing = auth_client.post("/api/internal/agent-tools/overview", json={})
    assert missing.status_code == 401
    assert missing.json()["code"] == "INVALID_AGENT_KEY"

    key_only = auth_client.post(
        "/api/internal/agent-tools/overview",
        headers={"X-Agent-Internal-Key": INTERNAL_KEY},
        json={},
    )
    assert key_only.status_code == 401
    assert key_only.json()["code"] == "AGENT_CONTEXT_REQUIRED"


def test_expired_and_wrong_purpose_context_are_rejected(
    auth_client: TestClient,
) -> None:
    uid = user_id(auth_client, "phase5_admin")
    now = datetime.now(UTC)
    for token in (
        create_agent_context_token(
            user_id=uid,
            conversation_id=None,
            secret=JWT_SECRET,
            expire_minutes=-1,
        ),
        jwt.encode(
            {
                "sub": str(uid),
                "purpose": "access",
                "iat": now,
                "exp": now + timedelta(minutes=5),
            },
            JWT_SECRET,
            algorithm=ALGORITHM,
        ),
    ):
        response = auth_client.post(
            "/api/internal/agent-tools/overview",
            headers={
                "X-Agent-Internal-Key": INTERNAL_KEY,
                "X-Agent-Context-Token": token,
            },
            json={},
        )
        assert response.status_code == 401
        assert response.json()["code"] == "INVALID_AGENT_CONTEXT"


def test_disabled_account_is_rechecked_from_database(auth_client: TestClient) -> None:
    engine = create_engine(get_settings().test_database_url)
    with engine.connect() as connection:
        disabled_id = connection.scalar(
            text("SELECT id FROM users WHERE username = 'phase5_disabled'")
        )
    engine.dispose()
    token = create_agent_context_token(
        user_id=disabled_id,
        conversation_id=None,
        secret=JWT_SECRET,
    )
    response = auth_client.post(
        "/api/internal/agent-tools/overview",
        headers={
            "X-Agent-Internal-Key": INTERNAL_KEY,
            "X-Agent-Context-Token": token,
        },
        json={},
    )
    assert response.status_code == 401
    assert response.json()["code"] == "ACCOUNT_UNAVAILABLE"

def test_admin_tools_match_public_statistics_service(auth_client: TestClient) -> None:
    headers = tool_headers(auth_client, "phase5_admin")
    cases = (
        ("overview", {}, "/api/statistics/overview"),
        ("club-ranking", {"limit": 5}, "/api/statistics/rankings/club?limit=5"),
        (
            "activity-ranking",
            {"limit": 5},
            "/api/statistics/rankings/activity?limit=5",
        ),
        ("trend", {}, "/api/statistics/trends/monthly"),
        (
            "distribution",
            {"dimension": "college"},
            "/api/statistics/distributions/college",
        ),
    )
    for tool, payload, public_path in cases:
        internal = auth_client.post(
            f"/api/internal/agent-tools/{tool}", headers=headers, json=payload
        )
        public = auth_client.get(public_path)
        assert internal.status_code == 200
        assert internal.json() == public.json()


def test_activity_category_filter_matches_public_statistics(
    auth_client: TestClient,
) -> None:
    headers = tool_headers(auth_client, "phase5_admin")
    engine = create_engine(get_settings().test_database_url)
    with engine.connect() as connection:
        category_id = connection.scalar(
            text("SELECT id FROM activity_categories ORDER BY id LIMIT 1")
        )
    engine.dispose()

    internal = auth_client.post(
        "/api/internal/agent-tools/activity-ranking",
        headers=headers,
        json={"category_id": category_id, "limit": 5},
    )
    public = auth_client.get(
        f"/api/statistics/rankings/activity?category_id={category_id}&limit=5"
    )
    assert internal.status_code == 200
    assert internal.json() == public.json()

def test_manager_is_limited_to_bound_club(auth_client: TestClient) -> None:
    headers = tool_headers(auth_client, "phase5_manager")
    engine = create_engine(get_settings().test_database_url)
    with engine.connect() as connection:
        managed = connection.scalar(
            text(
                "SELECT club_id FROM user_club_roles ur JOIN users u ON u.id = ur.user_id "
                "WHERE u.username = 'phase5_manager'"
            )
        )
        other = connection.scalar(
            text("SELECT id FROM clubs WHERE id <> :id ORDER BY id LIMIT 1"),
            {"id": managed},
        )
    engine.dispose()

    required = auth_client.post(
        "/api/internal/agent-tools/overview", headers=headers, json={}
    )
    allowed = auth_client.post(
        "/api/internal/agent-tools/club-summary",
        headers=headers,
        json={"club_id": managed},
    )
    forbidden = auth_client.post(
        "/api/internal/agent-tools/club-summary",
        headers=headers,
        json={"club_id": other},
    )
    assert required.status_code == 403
    assert required.json()["code"] == "CLUB_SCOPE_REQUIRED"
    assert allowed.status_code == 200
    assert forbidden.status_code == 403


def test_student_summary_forces_authenticated_student(auth_client: TestClient) -> None:
    headers = tool_headers(auth_client, "phase5_student")
    engine = create_engine(get_settings().test_database_url)
    with engine.connect() as connection:
        own = connection.scalar(
            text("SELECT student_id FROM users WHERE username = 'phase5_student'")
        )
        other = connection.scalar(
            text("SELECT id FROM students WHERE id <> :id ORDER BY id LIMIT 1"),
            {"id": own},
        )
    engine.dispose()

    response = auth_client.post(
        "/api/internal/agent-tools/student-summary",
        headers=headers,
        json={"student_id": other},
    )
    assert response.status_code == 200
    assert response.json()["id"] == own


def test_tool_inputs_forbid_unknown_fields_and_invalid_ranges(
    auth_client: TestClient,
) -> None:
    headers = tool_headers(auth_client, "phase5_admin")
    for payload in (
        {"unknown": 1},
        {"limit": 0},
        {"start_date": "2026-08-10", "end_date": "2026-08-01"},
    ):
        endpoint = "club-ranking" if "limit" in payload else "overview"
        response = auth_client.post(
            f"/api/internal/agent-tools/{endpoint}", headers=headers, json=payload
        )
        assert response.status_code == 422
        assert response.json()["code"] == "VALIDATION_ERROR"
