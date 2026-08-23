from __future__ import annotations

from app.agent.schemas import HermesReply, HermesToolCall
from app.core.security import decode_agent_context_token
from fastapi.testclient import TestClient


class FakeAgentHermesClient:
    def __init__(self) -> None:
        self.prompt = ""
        self.context_token = ""

    def chat(self, prompt: str, context_token: str | None = None) -> HermesReply:
        self.prompt = prompt
        self.context_token = context_token or ""
        return HermesReply(
            content="晴川书院相关社团中，青年志愿者协会活跃度最高。",
            model="qwen-test:latest",
            tool_calls=(
                HermesToolCall(
                    name="get_club_ranking",
                    arguments={"campus_id": 1, "limit": 3},
                    data=[
                        {
                            "id": 1,
                            "name": "青年志愿者协会",
                            "activity_score": 96.5,
                        },
                        {"id": 2, "name": "摄影协会", "activity_score": 82.0},
                    ],
                ),
            ),
        )


def login(client: TestClient, username: str) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": "Correct-Password-5"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_agent_chat_history_visualization_and_delete(auth_client: TestClient) -> None:
    hermes = FakeAgentHermesClient()
    auth_client.app.state.hermes_client = hermes
    headers = login(auth_client, "phase5_admin")

    chat = auth_client.post(
        "/api/agent/chat",
        headers=headers,
        json={
            "message": "晴川书院哪些社团最活跃？",
            "context": {"term_id": 1, "campus_id": 1},
        },
    )

    assert chat.status_code == 200
    body = chat.json()
    conversation_id = body["conversation_id"]
    assert body["tool_calls"][0]["name"] == "get_club_ranking"
    assert body["data"][0]["name"] == "青年志愿者协会"
    assert body["visualization"] == {
        "type": "bar",
        "title": "社团活跃排行",
        "categories": ["青年志愿者协会", "摄影协会"],
        "series": [{"name": "活跃度", "data": [96.5, 82.0]}],
    }
    claims = decode_agent_context_token(
        hermes.context_token, auth_client.app.state.settings.jwt_secret
    )
    assert claims.conversation_id == conversation_id
    assert "学期ID=1，校区ID=1" in hermes.prompt

    conversations = auth_client.get("/api/agent/conversations", headers=headers).json()
    assert conversations[0]["id"] == conversation_id
    assert conversations[0]["message_count"] == 2

    messages = auth_client.get(
        f"/api/agent/conversations/{conversation_id}/messages", headers=headers
    ).json()
    assert [message["role"] for message in messages] == ["user", "assistant"]
    assert messages[1]["tool_calls"][0]["name"] == "get_club_ranking"
    assert "data" not in messages[1]["tool_calls"][0]

    foreign_headers = login(auth_client, "phase5_manager")
    assert (
        auth_client.get(
            f"/api/agent/conversations/{conversation_id}/messages",
            headers=foreign_headers,
        ).status_code
        == 404
    )

    deleted = auth_client.delete(
        f"/api/agent/conversations/{conversation_id}", headers=headers
    )
    assert deleted.status_code == 204
    assert auth_client.get("/api/agent/conversations", headers=headers).json() == []


def test_agent_chat_rejects_unknown_fields(auth_client: TestClient) -> None:
    response = auth_client.post(
        "/api/agent/chat",
        headers=login(auth_client, "phase5_admin"),
        json={"message": "统计", "temperature": 0.9},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
