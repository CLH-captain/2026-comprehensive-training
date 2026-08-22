from __future__ import annotations

import subprocess

import pytest
from app.agent.hermes import HermesClient
from app.core.errors import AppError


def make_client(tmp_path, runner) -> HermesClient:
    executable = tmp_path / "hermes.exe"
    executable.touch()
    return HermesClient(
        executable=str(executable),
        provider="custom:local",
        model="qwen-test:latest",
        hermes_home=str(tmp_path),
        working_directory=str(tmp_path),
        timeout_seconds=5,
        dashboard_url="http://127.0.0.1:9120",
        ollama_url="http://127.0.0.1:11434/v1",
        runner=runner,
    )


def test_chat_uses_argument_array_and_returns_clean_reply(tmp_path) -> None:
    captured = {}

    def runner(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(command, 0, "  连接成功\n", "")

    client = make_client(tmp_path, runner)
    reply = client.chat("只回复连接成功")

    assert reply.content == "连接成功"
    assert reply.model == "qwen-test:latest"
    assert captured["command"][1:3] == ("--oneshot", "只回复连接成功")
    assert captured["kwargs"]["shell"] is False


def test_chat_maps_timeout_to_safe_app_error(tmp_path) -> None:
    def runner(command, **kwargs):
        raise subprocess.TimeoutExpired(command, kwargs["timeout"])

    with pytest.raises(AppError) as caught:
        make_client(tmp_path, runner).chat("hello")

    assert caught.value.status_code == 504
    assert caught.value.code == "HERMES_TIMEOUT"


@pytest.mark.parametrize(
    ("result", "code"),
    [
        (subprocess.CompletedProcess([], 1, "", "connection refused"), "HERMES_FAILED"),
        (subprocess.CompletedProcess([], 0, "  ", ""), "HERMES_EMPTY_RESPONSE"),
    ],
)
def test_chat_rejects_failed_or_empty_result(tmp_path, result, code) -> None:
    with pytest.raises(AppError) as caught:
        make_client(tmp_path, lambda *args, **kwargs: result).chat("hello")

    assert caught.value.code == code


def test_missing_runtime_is_reported_without_starting_process(tmp_path) -> None:
    client = HermesClient(
        executable=str(tmp_path / "missing.exe"),
        provider="custom:local",
        model="qwen-test:latest",
        hermes_home=str(tmp_path),
        working_directory=str(tmp_path),
        timeout_seconds=5,
        dashboard_url="http://127.0.0.1:9120",
        ollama_url="http://127.0.0.1:11434/v1",
    )

    with pytest.raises(AppError) as caught:
        client.chat("hello")

    assert caught.value.code == "HERMES_RUNTIME_MISSING"