from __future__ import annotations

import subprocess
from pathlib import Path

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


def test_chat_passes_agent_context_only_through_child_environment(tmp_path) -> None:
    captured = {}

    def runner(command, **kwargs):
        captured.update(kwargs)
        return subprocess.CompletedProcess(command, 0, "完成", "")

    client = make_client(tmp_path, runner)
    client.agent_internal_key = "internal-test-key"
    client.agent_tool_base_url = "http://127.0.0.1:8000"
    client.chat("统计", context_token="context-test-token")

    assert "context-test-token" not in client.command("统计")
    assert captured["env"]["SZUT_AGENT_CONTEXT_TOKEN"] == "context-test-token"
    assert captured["env"]["AGENT_INTERNAL_KEY"] == "internal-test-key"


def test_chat_reads_tool_trace_and_removes_temporary_file(tmp_path) -> None:
    captured_trace_path = None

    def runner(command, **kwargs):
        nonlocal captured_trace_path
        captured_trace_path = Path(kwargs["env"]["SZUT_AGENT_TRACE_FILE"])
        captured_trace_path.write_text(
            '{"name":"statistics_overview","arguments":{"term_id":1},'
            '"data":{"student_count":100},"success":true}\n',
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(command, 0, "统计完成", "")

    reply = make_client(tmp_path, runner).chat("统计概览")

    assert len(reply.tool_calls) == 1
    assert reply.tool_calls[0].name == "statistics_overview"
    assert reply.tool_calls[0].data == {"student_count": 100}
    assert captured_trace_path is not None
    assert not captured_trace_path.exists()


def test_chat_ignores_damaged_trace_records(tmp_path) -> None:
    def runner(command, **kwargs):
        Path(kwargs["env"]["SZUT_AGENT_TRACE_FILE"]).write_text(
            'not-json\n{"name":42,"arguments":{}}\n', encoding="utf-8"
        )
        return subprocess.CompletedProcess(command, 0, "完成", "")

    assert make_client(tmp_path, runner).chat("统计").tool_calls == ()


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
