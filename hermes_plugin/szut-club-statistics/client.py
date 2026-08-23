from __future__ import annotations

import json
import os
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class ToolClient:
    base_url: str
    internal_key: str
    context_token: str
    timeout: float = 20.0

    @classmethod
    def from_env(cls) -> ToolClient:
        values = {
            "base_url": os.getenv("SZUT_API_BASE_URL", "http://127.0.0.1:8000"),
            "internal_key": os.getenv("AGENT_INTERNAL_KEY", ""),
            "context_token": os.getenv("SZUT_AGENT_CONTEXT_TOKEN", ""),
        }
        if not values["internal_key"] or not values["context_token"]:
            raise RuntimeError("Agent internal credentials are not configured")
        return cls(**values)

    def call(self, endpoint: str, payload: dict[str, object]) -> object:
        request = Request(
            f"{self.base_url.rstrip('/')}/api/internal/agent-tools/{endpoint}",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "X-Agent-Internal-Key": self.internal_key,
                "X-Agent-Context-Token": self.context_token,
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            try:
                detail = json.loads(exc.read().decode("utf-8"))
                message = detail.get("message", "Tool request failed")
            except (UnicodeDecodeError, json.JSONDecodeError):
                message = "Tool request failed"
            raise RuntimeError(message) from exc
        except URLError as exc:
            raise RuntimeError("FastAPI Agent Tool service is unavailable") from exc
