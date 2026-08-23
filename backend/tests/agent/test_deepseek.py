from __future__ import annotations

import httpx
import pytest
from app.agent.deepseek import DeepSeekClient
from app.agent.fallback import allows_fallback, is_recoverable_local_error
from app.core.errors import AppError


def test_fallback_policy_only_allows_admin_aggregate_questions() -> None:
    assert allows_fallback("admin", "本学期社团参与情况如何")
    assert not allows_fallback("student", "本学期社团参与情况如何")
    assert not allows_fallback("admin", "我的个人签到明细")
    assert is_recoverable_local_error(AppError(504, "HERMES_TIMEOUT", "timeout"))
    assert not is_recoverable_local_error(AppError(403, "FORBIDDEN", "forbidden"))


def test_deepseek_client_sends_only_aggregate_snapshot() -> None:
    captured: dict[str, object] = {}

    def post(url: str, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        request = httpx.Request("POST", url)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "已根据聚合数据完成分析。"}}]},
            request=request,
        )

    client = DeepSeekClient(
        base_url="https://api.deepseek.example/v1",
        api_key="test-key",
        model="deepseek-test",
        timeout_seconds=12,
        post=post,
    )
    reply = client.chat(
        question="本学期情况如何？",
        snapshot={"overview": {"active_clubs": 45, "participations": 16028}},
    )

    assert reply.model == "deepseek-test"
    assert reply.adapter == "deepseek_fallback"
    assert captured["url"] == "https://api.deepseek.example/chat/completions"
    body = captured["json"]
    assert isinstance(body, dict)
    user_text = body["messages"][1]["content"]
    assert "16028" in user_text
    assert "test-key" not in user_text
    assert "Authorization" in captured["headers"]


def test_deepseek_client_maps_http_failure_to_safe_error() -> None:
    def post(url: str, **kwargs):
        request = httpx.Request("POST", url)
        return httpx.Response(401, json={"error": "bad key"}, request=request)

    client = DeepSeekClient(
        base_url="https://api.deepseek.example/v1",
        api_key="test-key",
        model="deepseek-test",
        timeout_seconds=12,
        post=post,
    )

    with pytest.raises(AppError) as caught:
        client.chat(question="统计", snapshot={"overview": {}})

    assert caught.value.code == "DEEPSEEK_UNAVAILABLE"
