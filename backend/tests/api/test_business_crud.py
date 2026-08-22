from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.core.config import get_settings


def admin_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"username": "phase5_admin", "password": "Correct-Password-5"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_admin_business_crud_round_trip(auth_client: TestClient) -> None:
    engine = create_engine(get_settings().test_database_url)
    headers = admin_headers(auth_client)
    ids: dict[str, int] = {}
    with engine.connect() as connection:
        context = connection.execute(
            text(
                """
                SELECT co.id AS college_id, m.id AS major_id,
                       cc.id AS club_category_id, ac.id AS activity_category_id,
                       ca.id AS campus_id, t.id AS term_id, v.id AS venue_id
                FROM colleges co JOIN majors m ON m.college_id = co.id
                CROSS JOIN club_categories cc CROSS JOIN activity_categories ac
                CROSS JOIN campuses ca CROSS JOIN academic_terms t CROSS JOIN venues v
                LIMIT 1
                """
            )
        ).mappings().one()
    try:
        student = auth_client.post(
            "/api/students",
            headers=headers,
            json={
                "student_no": "P5-CRUD-0001",
                "name": "阶段五测试学生",
                "gender": "男",
                "college_id": context["college_id"],
                "major_id": context["major_id"],
                "enrollment_year": 2026,
                "grade_no": 1,
                "class_name": "测试班",
            },
        )
        assert student.status_code == 201, student.text
        ids["student"] = student.json()["id"]


        club = auth_client.post(
            "/api/clubs",
            headers=headers,
            json={
                "code": "P5-CLUB-001",
                "name": "阶段五接口测试社团",
                "category_id": context["club_category_id"],
                "home_campus_id": context["campus_id"],
                "leader_student_id": ids["student"],
                "advisor_name": "测试教师",
            },
        )
        assert club.status_code == 201, club.text
        ids["club"] = club.json()["id"]

        membership = auth_client.put(
            f"/api/clubs/{ids['club']}/members",
            headers=headers,
            json={
                "student_id": ids["student"],
                "role": "leader",
                "join_date": "2026-08-22",
            },
        )
        assert membership.status_code == 200, membership.text

        start = datetime(2026, 9, 10, 14, 0, tzinfo=UTC)
        activity = auth_client.post(
            "/api/activities",
            headers=headers,
            json={
                "code": "P5-ACT-001",
                "club_id": ids["club"],
                "category_id": context["activity_category_id"],
                "term_id": context["term_id"],
                "venue_id": context["venue_id"],
                "title": "阶段五接口闭环活动",
                "start_time": start.isoformat(),
                "end_time": (start + timedelta(hours=2)).isoformat(),
                "capacity": 30,
                "status": "published",
            },
        )
        assert activity.status_code == 201, activity.text
        ids["activity"] = activity.json()["id"]

        registration = auth_client.post(
            "/api/registrations",
            headers=headers,
            json={"activity_id": ids["activity"], "student_id": ids["student"]},
        )
        assert registration.status_code == 201, registration.text
        ids["registration"] = registration.json()["id"]

        attendance = auth_client.put(
            "/api/attendance",
            headers=headers,
            json={
                "activity_id": ids["activity"],
                "student_id": ids["student"],
                "status": "present",
            },
        )
        assert attendance.status_code == 200, attendance.text

        records = auth_client.get(
            f"/api/attendance?activity_id={ids['activity']}", headers=headers
        )
        assert records.status_code == 200
        assert records.json()["total"] == 1

        updated = auth_client.put(
            f"/api/students/{ids['student']}",
            headers=headers,
            json={"class_name": "测试班（已编辑）"},
        )
        assert updated.status_code == 200
        assert updated.json()["class_name"] == "测试班（已编辑）"

        deleted = auth_client.delete(
            f"/api/activities/{ids['activity']}", headers=headers
        )
        assert deleted.status_code == 200
        assert deleted.json()["result"] == "cancelled"
    finally:
        with engine.begin() as connection:
            if "activity" in ids:
                connection.execute(
                    text("DELETE FROM activity_attendance WHERE activity_id = :id"),
                    {"id": ids["activity"]},
                )
                connection.execute(
                    text("DELETE FROM activity_registrations WHERE activity_id = :id"),
                    {"id": ids["activity"]},
                )
                connection.execute(
                    text("DELETE FROM activities WHERE id = :id"),
                    {"id": ids["activity"]},
                )
            if "club" in ids:
                connection.execute(
                    text("DELETE FROM club_memberships WHERE club_id = :id"),
                    {"id": ids["club"]},
                )
                connection.execute(
                    text("DELETE FROM clubs WHERE id = :id"), {"id": ids["club"]}
                )
            if "student" in ids:
                connection.execute(
                    text("DELETE FROM students WHERE id = :id"),
                    {"id": ids["student"]},
                )
        engine.dispose()


def test_admin_can_create_and_disable_dictionary(auth_client: TestClient) -> None:
    engine = create_engine(get_settings().test_database_url)
    headers = admin_headers(auth_client)
    category_id: int | None = None
    try:
        created = auth_client.post(
            "/api/dictionaries/activity-categories",
            headers=headers,
            json={"name": "阶段五临时分类", "description": "接口测试"},
        )
        assert created.status_code == 201, created.text
        category_id = created.json()["id"]
        deleted = auth_client.delete(
            f"/api/dictionaries/activity-categories/{category_id}", headers=headers
        )
        assert deleted.status_code == 204
        with engine.connect() as connection:
            assert connection.scalar(
                text("SELECT is_active FROM activity_categories WHERE id = :id"),
                {"id": category_id},
            ) == 0
    finally:
        if category_id is not None:
            with engine.begin() as connection:
                connection.execute(
                    text("DELETE FROM activity_categories WHERE id = :id"),
                    {"id": category_id},
                )
        engine.dispose()
