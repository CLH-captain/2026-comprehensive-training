from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from app.core.config import get_settings
from app.main import create_app


@pytest.fixture(scope="module")
def statistics_client() -> Iterator[TestClient]:
    app: FastAPI = create_app()
    original_engine = app.state.engine
    app.state.engine = create_engine(get_settings().test_database_url)
    with TestClient(app) as client:
        yield client
    app.state.engine.dispose()
    original_engine.dispose()


def test_dashboard_contract_remains_compatible(statistics_client: TestClient) -> None:
    response = statistics_client.get("/api/statistics/dashboard")

    assert response.status_code == 200
    payload = response.json()
    assert payload["overview"]["participations"] == 16028
    assert len(payload["club_ranking"]) == 8
    assert len(payload["top_activities"]) == 6
    assert payload["contexts"]["terms"]


@pytest.mark.parametrize("dimension", ["club", "activity", "student", "college"])
def test_ranking_api_dimensions(statistics_client: TestClient, dimension: str) -> None:
    response = statistics_client.get(f"/api/statistics/rankings/{dimension}?limit=3")

    assert response.status_code == 200
    assert len(response.json()) == 3


@pytest.mark.parametrize("dimension", ["category", "college", "campus"])
def test_distribution_api_dimensions(statistics_client: TestClient, dimension: str) -> None:
    response = statistics_client.get(f"/api/statistics/distributions/{dimension}")

    assert response.status_code == 200
    assert response.json()


def test_summary_api_returns_404(statistics_client: TestClient) -> None:
    assert statistics_client.get("/api/statistics/students/999999").status_code == 404
    assert statistics_client.get("/api/statistics/clubs/999999").status_code == 404


def test_invalid_date_range_returns_422(statistics_client: TestClient) -> None:
    response = statistics_client.get(
        "/api/statistics/overview?date_from=2026-04-01&date_to=2026-03-01"
    )

    assert response.status_code == 422
