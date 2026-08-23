from __future__ import annotations

import json
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


def invoke(tool_name: str, args: dict[str, Any]) -> str:
    try:
        data = ToolClient.from_env().call(ENDPOINTS[tool_name], args)
        return json.dumps({"success": True, "data": data}, ensure_ascii=False)
    except (KeyError, RuntimeError) as exc:
        return json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False)


def handler_for(tool_name: str):
    def handler(args: dict[str, Any], **_kwargs) -> str:
        return invoke(tool_name, args)

    return handler
