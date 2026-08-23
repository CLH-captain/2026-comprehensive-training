from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .client import ToolClient

ENDPOINTS = {
    "get_overview_statistics": "overview",
    "get_club_ranking": "club-ranking",
    "get_activity_ranking": "activity-ranking",
    "get_participation_trend": "trend",
    "get_distribution_statistics": "distribution",
    "get_student_summary": "student-summary",
    "get_club_summary": "club-summary",
}


def _trace(record: dict[str, Any]) -> None:
    trace_path = os.getenv("SZUT_AGENT_TRACE_FILE")
    if not trace_path:
        return
    with Path(trace_path).open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")


def invoke(tool_name: str, args: dict[str, Any]) -> str:
    try:
        data = ToolClient.from_env().call(ENDPOINTS[tool_name], args)
        _trace(
            {
                "name": tool_name,
                "arguments": args,
                "data": data,
                "success": True,
            }
        )
        return json.dumps({"success": True, "data": data}, ensure_ascii=False)
    except (KeyError, RuntimeError) as exc:
        _trace(
            {
                "name": tool_name,
                "arguments": args,
                "data": None,
                "success": False,
                "error": str(exc),
            }
        )
        return json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False)


def handler_for(tool_name: str):
    def handler(args: dict[str, Any], **_kwargs) -> str:
        return invoke(tool_name, args)

    return handler