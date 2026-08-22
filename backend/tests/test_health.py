from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_health_returns_service_identity() -> None:
    settings = Settings(
        app_env="test",
        database_url="mysql+pymysql://user:pass@127.0.0.1/test",
        test_database_url="mysql+pymysql://user:pass@127.0.0.1/test",
        jwt_secret="x" * 32,
        hermes_api_key="test-hermes-key",
        agent_internal_key="x" * 32,
        deepseek_api_key="test-deepseek-key",
    )
    client = TestClient(create_app(settings))

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "SZUT Club Activity Agent",
        "environment": "test",
    }
