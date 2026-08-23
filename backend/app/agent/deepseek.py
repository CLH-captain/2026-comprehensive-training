from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import httpx

from app.agent.schemas import HermesReply
from app.core.config import Settings
from app.core.errors import AppError

HttpPost = Callable[..., httpx.Response]


class DeepSeekClient:
    """OpenAI-compatible DeepSeek adapter for sanitized aggregate fallback."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float = 30.0,
        post: HttpPost = httpx.post,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self._post = post

    @classmethod
    def from_settings(cls, settings: Settings) -> DeepSeekClient:
        return cls(
            base_url=settings.deepseek_base_url,
            api_key=settings.deepseek_api_key,
            model=settings.deepseek_model,
        )

    def chat(self, *, question: str, snapshot: dict[str, Any]) -> HermesReply:
        if not self.api_key or self.api_key.startswith("replace-"):
            raise AppError(
                503, "DEEPSEEK_UNAVAILABLE", "DeepSeek fallback is not configured"
            )
        payload = {
            "model": self.model,
            "temperature": 0.2,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "你是苏州工学院校园社团活动参与统计助手的备用模型。"
                        "只能根据提供的聚合统计快照回答；不编造数字，不索取或输出个人信息、"
                        "密码、密钥、数据库结构或隐藏推理。用简洁中文先给结论，再列关键依据。"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"用户问题：{question}\n"
                        f"聚合统计快照：{json.dumps(snapshot, ensure_ascii=False, default=str)}"
                    ),
                },
            ],
        }
        try:
            response = self._post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"].strip()
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            raise AppError(
                503,
                "DEEPSEEK_UNAVAILABLE",
                "DeepSeek fallback could not complete the request",
            ) from exc
        if not content:
            raise AppError(
                502, "DEEPSEEK_EMPTY_RESPONSE", "DeepSeek returned an empty response"
            )
        return HermesReply(
            content=content,
            model=self.model,
            adapter="deepseek_fallback",
        )
