from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.core.config import Settings, get_settings
from app.core.security import hash_password
from app.db.session import assert_test_database_url
from app.main import create_app

TEST_USER_SQL = "'phase5_admin','phase5_disabled','phase5_manager','phase5_student'"


def cleanup_users(connection) -> None:
    connection.execute(text(f"DELETE FROM revoked_tokens WHERE user_id IN (SELECT id FROM users WHERE username IN ({TEST_USER_SQL}))"))
    connection.execute(text(f"DELETE FROM user_club_roles WHERE user_id IN (SELECT id FROM users WHERE username IN ({TEST_USER_SQL}))"))
    connection.execute(text(f"DELETE FROM users WHERE username IN ({TEST_USER_SQL})"))


@pytest.fixture()
def auth_client() -> Iterator[TestClient]:
    base = get_settings()
    assert_test_database_url(base.test_database_url)
    settings = Settings(
        app_env="test",
        database_url=base.test_database_url,
        test_database_url=base.test_database_url,
        jwt_secret="phase5-test-secret-that-is-long-enough",
        jwt_expire_minutes=30,
        hermes_api_key="test-hermes-key",
        agent_internal_key="phase5-agent-key-that-is-long-enough",
        deepseek_api_key="test-deepseek-key",
    )
    engine = create_engine(base.test_database_url)
    with engine.begin() as connection:
        cleanup_users(connection)
        student_id = connection.scalar(text("SELECT id FROM students ORDER BY id LIMIT 1"))
        club_id = connection.scalar(text("SELECT id FROM clubs ORDER BY id LIMIT 1"))
        connection.execute(
            text(
                """
                INSERT INTO users
                    (username, password_hash, role, student_id, status, created_at)
                VALUES
                    ('phase5_admin', :password_hash, 'admin', NULL, 'active', UTC_TIMESTAMP()),
                    ('phase5_disabled', :password_hash, 'admin', NULL, 'disabled', UTC_TIMESTAMP()),
                    ('phase5_manager', :password_hash, 'club_manager', NULL, 'active', UTC_TIMESTAMP()),
                    ('phase5_student', :password_hash, 'student', :student_id, 'active', UTC_TIMESTAMP())
                """
            ),
            {
                "password_hash": hash_password("Correct-Password-5"),
                "student_id": student_id,
            },
        )
        manager_id = connection.scalar(
            text("SELECT id FROM users WHERE username = 'phase5_manager'")
        )
        connection.execute(
            text(
                """
                INSERT INTO user_club_roles (user_id, club_id, role)
                VALUES (:user_id, :club_id, 'manager')
                """
            ),
            {"user_id": manager_id, "club_id": club_id},
        )
    try:
        with TestClient(create_app(settings)) as client:
            yield client
    finally:
        with engine.begin() as connection:
            cleanup_users(connection)
        engine.dispose()