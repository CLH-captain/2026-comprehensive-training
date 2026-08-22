from fastapi.testclient import TestClient

from app.main import create_app


def test_students_list_returns_real_pagination() -> None:
    response = TestClient(create_app()).get("/api/students?page=1&page_size=20&grade_no=1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["page"] == 1
    assert payload["page_size"] == 20
    assert payload["total"] > 0
    assert len(payload["items"]) == 20
    assert all(item["grade_no"] == 1 for item in payload["items"])


def test_students_list_supports_search() -> None:
    client = TestClient(create_app())
    first_student = client.get("/api/students?page_size=1").json()["items"][0]

    response = client.get("/api/students", params={"search": first_student["student_no"]})

    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_student_detail_returns_participation_summary() -> None:
    client = TestClient(create_app())
    student_id = client.get("/api/students?page_size=1").json()["items"][0]["id"]

    response = client.get(f"/api/students/{student_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == student_id
    assert "participation_summary" in payload
    assert "recent_activities" in payload
    assert "clubs" in payload


def test_student_detail_returns_404_for_unknown_student() -> None:
    response = TestClient(create_app()).get("/api/students/999999")

    assert response.status_code == 404
