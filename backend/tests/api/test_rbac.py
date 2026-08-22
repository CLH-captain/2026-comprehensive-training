import pytest

from app.core.errors import AppError
from app.core.permissions import AccessScope, require_role


def test_admin_scope_allows_all_entities() -> None:
    scope = AccessScope(1, "admin", None, None)
    assert scope.permits_club(999)
    assert scope.permits_student(999)


def test_club_manager_scope_only_allows_bound_clubs() -> None:
    scope = AccessScope(2, "club_manager", None, frozenset({3, 5}))
    assert scope.permits_club(3)
    with pytest.raises(AppError) as caught:
        scope.require_club(4)
    assert caught.value.status_code == 403


def test_student_scope_only_allows_self() -> None:
    scope = AccessScope(3, "student", 88, frozenset())
    scope.require_student(88)
    with pytest.raises(AppError):
        scope.require_student(89)
    assert not scope.permits_club(1)


def test_role_requirement_rejects_wrong_role() -> None:
    scope = AccessScope(3, "student", 88, frozenset())
    with pytest.raises(AppError) as caught:
        require_role(scope, "admin")
    assert caught.value.code == "FORBIDDEN"


def login_as(client, username: str) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": "Correct-Password-5"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_club_manager_api_is_limited_to_bound_club(auth_client) -> None:
    from sqlalchemy import create_engine, text

    from app.core.config import get_settings

    engine = create_engine(get_settings().test_database_url)
    with engine.connect() as connection:
        bound_id = connection.scalar(text("SELECT club_id FROM user_club_roles ucr JOIN users u ON u.id = ucr.user_id WHERE u.username = 'phase5_manager'"))
        other_id = connection.scalar(text("SELECT id FROM clubs WHERE id <> :id ORDER BY id LIMIT 1"), {"id": bound_id})
    engine.dispose()
    headers = login_as(auth_client, "phase5_manager")
    assert auth_client.get(f"/api/clubs/{bound_id}/members", headers=headers).status_code == 200
    denied = auth_client.get(f"/api/clubs/{other_id}/members", headers=headers)
    assert denied.status_code == 403
    assert denied.json()["code"] == "FORBIDDEN"


def test_student_api_only_returns_own_participation(auth_client) -> None:
    headers = login_as(auth_client, "phase5_student")
    me = auth_client.get("/api/auth/me", headers=headers).json()
    response = auth_client.get("/api/registrations", headers=headers)
    assert response.status_code == 200
    assert all(item["student_id"] == me["student_id"] for item in response.json()["items"])


def test_manager_cannot_create_admin_dictionary(auth_client) -> None:
    headers = login_as(auth_client, "phase5_manager")
    response = auth_client.post(
        "/api/dictionaries/activity-categories",
        headers=headers,
        json={"name": "不可创建的分类"},
    )
    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"

def test_student_statistics_summary_is_limited_to_self(auth_client) -> None:
    from sqlalchemy import create_engine, text

    from app.core.config import get_settings

    headers = login_as(auth_client, "phase5_student")
    me = auth_client.get("/api/auth/me", headers=headers).json()
    own = auth_client.get(
        f"/api/statistics/students/{me['student_id']}", headers=headers
    )
    assert own.status_code == 200
    engine = create_engine(get_settings().test_database_url)
    with engine.connect() as connection:
        other_id = connection.scalar(
            text("SELECT id FROM students WHERE id <> :id ORDER BY id LIMIT 1"),
            {"id": me["student_id"]},
        )
    engine.dispose()
    denied = auth_client.get(f"/api/statistics/students/{other_id}", headers=headers)
    assert denied.status_code == 403