from __future__ import annotations

import json
import logging

from app.agent.acceptance import AGENT_ACCEPTANCE_QUESTIONS, VALID_TOOLS
from app.core.logging import JsonFormatter


def test_acceptance_question_set_has_forty_unique_valid_questions() -> None:
    assert len(AGENT_ACCEPTANCE_QUESTIONS) == 40
    assert len({item.id for item in AGENT_ACCEPTANCE_QUESTIONS}) == 40
    assert {item.expected_tool for item in AGENT_ACCEPTANCE_QUESTIONS} <= VALID_TOOLS
    assert all(item.question and item.category for item in AGENT_ACCEPTANCE_QUESTIONS)


def test_json_logs_only_safe_structured_fields() -> None:
    record = logging.makeLogRecord(
        {
            "msg": "agent.completed",
            "request_id": "req-1",
            "source": "local",
            "model": "qwen",
            "fallback": False,
            "prompt": "must not be logged",
            "api_key": "must not be logged",
        }
    )
    payload = json.loads(JsonFormatter().format(record))

    assert payload["event"] == "agent.completed"
    assert payload["request_id"] == "req-1"
    assert payload["source"] == "local"
    assert "prompt" not in payload
    assert "api_key" not in payload
