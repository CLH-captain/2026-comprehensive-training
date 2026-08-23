from app.agent.schemas import HermesReply, RuntimeStatus
from fastapi.testclient import TestClient


class FakeHermesClient:
    def status(self) -> RuntimeStatus:
        return RuntimeStatus(
            runtime_available=True,
            dashboard_available=True,
            ollama_available=True,
            model_available=True,
            model="qwen-test:latest",
            hermes_version="0.19.0",
        )

    def chat(self, prompt: str) -> HermesReply:
        return HermesReply(content=f"收到：{prompt}", model="qwen-test:latest")


def login(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"username": "phase5_admin", "password": "Correct-Password-5"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_runtime_endpoints_require_authentication(auth_client: TestClient) -> None:
    assert auth_client.get("/api/agent/runtime").status_code == 401
    assert (
        auth_client.post(
            "/api/agent/runtime/chat", json={"message": "hello"}
        ).status_code
        == 401
    )


def test_runtime_status_and_basic_chat(auth_client: TestClient) -> None:
    auth_client.app.state.hermes_client = FakeHermesClient()
    headers = login(auth_client)

    status = auth_client.get("/api/agent/runtime", headers=headers)
    chat = auth_client.post(
        "/api/agent/runtime/chat",
        headers=headers,
        json={"message": "你好"},
    )

    assert status.status_code == 200
    assert status.json()["ready"] is True
    assert status.json()["hermes_version"] == "0.19.0"
    assert chat.status_code == 200
    assert chat.json() == {
        "content": "收到：你好",
        "model": "qwen-test:latest",
        "tool_calls": [],
        "adapter": "hermes_cli",
    }


def test_runtime_chat_rejects_unknown_fields(auth_client: TestClient) -> None:
    auth_client.app.state.hermes_client = FakeHermesClient()
    response = auth_client.post(
        "/api/agent/runtime/chat",
        headers=login(auth_client),
        json={"message": "hello", "model": "override"},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
