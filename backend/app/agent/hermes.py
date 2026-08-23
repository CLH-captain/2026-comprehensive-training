from __future__ import annotations

import json
import os
import subprocess
import tempfile
from collections.abc import Callable, Sequence
from pathlib import Path

import httpx

from app.agent.schemas import HermesReply, HermesToolCall, RuntimeStatus
from app.core.config import Settings
from app.core.errors import AppError

ProcessRunner = Callable[..., subprocess.CompletedProcess[str]]


class HermesClient:
    """Stable adapter around the programmatic CLI shipped with Hermes Desktop."""

    def __init__(
        self,
        *,
        executable: str,
        provider: str,
        model: str,
        hermes_home: str,
        working_directory: str,
        timeout_seconds: float,
        dashboard_url: str,
        ollama_url: str,
        agent_internal_key: str = "",
        agent_tool_base_url: str = "http://127.0.0.1:8000",
        toolsets: str = "szut_club_statistics",
        runner: ProcessRunner = subprocess.run,
    ) -> None:
        self.executable = Path(executable)
        self.provider = provider
        self.model = model
        self.hermes_home = Path(hermes_home)
        self.working_directory = Path(working_directory).resolve()
        self.timeout_seconds = timeout_seconds
        self.dashboard_url = dashboard_url.rstrip("/")
        self.ollama_url = ollama_url.removesuffix("/v1").rstrip("/")
        self.agent_internal_key = agent_internal_key
        self.agent_tool_base_url = agent_tool_base_url.rstrip("/")
        self.toolsets = toolsets
        self._runner = runner

    @classmethod
    def from_settings(cls, settings: Settings) -> HermesClient:
        return cls(
            executable=settings.hermes_executable,
            provider=settings.hermes_provider,
            model=settings.local_llm_model,
            hermes_home=settings.hermes_home,
            working_directory=settings.hermes_working_directory,
            timeout_seconds=settings.hermes_timeout_seconds,
            dashboard_url=settings.hermes_base_url,
            ollama_url=settings.local_llm_base_url,
            agent_internal_key=settings.agent_internal_key,
            agent_tool_base_url=settings.agent_tool_base_url,
            toolsets=settings.hermes_toolsets,
        )

    def command(self, prompt: str) -> Sequence[str]:
        return (
            str(self.executable),
            "--oneshot",
            prompt,
            "--provider",
            self.provider,
            "--model",
            self.model,
            "--toolsets",
            self.toolsets,
            "--ignore-rules",
        )

    def chat(self, prompt: str, context_token: str | None = None) -> HermesReply:
        if not self.executable.is_file():
            raise AppError(
                503, "HERMES_RUNTIME_MISSING", "Hermes Runtime is not available"
            )
        with tempfile.NamedTemporaryFile(
            prefix="szut-agent-", suffix=".jsonl", delete=False
        ) as trace_stream:
            trace_path = Path(trace_stream.name)
        try:
            result = self._run(prompt, context_token, trace_path)
            content = result.stdout.strip()
            if result.returncode != 0:
                raise AppError(
                    503, "HERMES_FAILED", self._safe_failure_message(result.stderr)
                )
            if not content:
                raise AppError(
                    502, "HERMES_EMPTY_RESPONSE", "Hermes returned an empty response"
                )
            return HermesReply(
                content=content,
                model=self.model,
                tool_calls=self._read_trace(trace_path),
            )
        finally:
            trace_path.unlink(missing_ok=True)

    def _run(
        self, prompt: str, context_token: str | None, trace_path: Path
    ) -> subprocess.CompletedProcess[str]:
        try:
            return self._runner(
                self.command(prompt),
                cwd=self.working_directory,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env={
                    **os.environ,
                    "HERMES_HOME": str(self.hermes_home),
                    "SZUT_API_BASE_URL": self.agent_tool_base_url,
                    "AGENT_INTERNAL_KEY": self.agent_internal_key,
                    "SZUT_AGENT_TRACE_FILE": str(trace_path),
                    **(
                        {"SZUT_AGENT_CONTEXT_TOKEN": context_token}
                        if context_token
                        else {}
                    ),
                },
                timeout=self.timeout_seconds,
                check=False,
                shell=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise AppError(
                504, "HERMES_TIMEOUT", "Local Agent response timed out"
            ) from exc
        except OSError as exc:
            raise AppError(
                503, "HERMES_START_FAILED", "Hermes Runtime could not be started"
            ) from exc

    @staticmethod
    def _read_trace(trace_path: Path) -> tuple[HermesToolCall, ...]:
        calls: list[HermesToolCall] = []
        for line in trace_path.read_text(encoding="utf-8").splitlines():
            try:
                item = json.loads(line)
                if not isinstance(item.get("name"), str) or not isinstance(
                    item.get("arguments"), dict
                ):
                    continue
                calls.append(
                    HermesToolCall(
                        name=item["name"],
                        arguments=item["arguments"],
                        data=item.get("data"),
                        success=bool(item.get("success", True)),
                        error=item.get("error"),
                    )
                )
            except (AttributeError, json.JSONDecodeError, TypeError):
                continue
        return tuple(calls)

    def status(self) -> RuntimeStatus:
        runtime_available = self.executable.is_file()
        version = self._runtime_version() if runtime_available else None
        dashboard_available = self._endpoint_ok(f"{self.dashboard_url}/api/status")
        ollama_available, model_available = self._ollama_status()
        return RuntimeStatus(
            runtime_available=runtime_available,
            dashboard_available=dashboard_available,
            ollama_available=ollama_available,
            model_available=model_available,
            model=self.model,
            hermes_version=version,
        )

    def _runtime_version(self) -> str | None:
        try:
            result = self._runner(
                (str(self.executable), "--version"),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                check=False,
                shell=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        lines = result.stdout.strip().splitlines()
        return lines[0] if lines else None

    def _endpoint_ok(self, url: str) -> bool:
        try:
            return httpx.get(url, timeout=2.0).is_success
        except httpx.HTTPError:
            return False

    def _ollama_status(self) -> tuple[bool, bool]:
        try:
            response = httpx.get(f"{self.ollama_url}/api/tags", timeout=3.0)
            response.raise_for_status()
        except httpx.HTTPError:
            return False, False
        names = {
            item.get("name")
            for item in response.json().get("models", [])
            if isinstance(item, dict)
        }
        return True, self.model in names

    @staticmethod
    def _safe_failure_message(stderr: str) -> str:
        lowered = stderr.lower()
        if "connection" in lowered or "connect" in lowered:
            return "Hermes could not connect to the local model"
        if "model" in lowered and ("not found" in lowered or "missing" in lowered):
            return "The configured local model is not available"
        return "Hermes could not complete the request"