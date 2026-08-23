from __future__ import annotations

from typing import Any

FILTER_PROPERTIES: dict[str, Any] = {
    "term_id": {"type": "integer", "minimum": 1},
    "campus_id": {"type": "integer", "minimum": 1},
    "college_id": {"type": "integer", "minimum": 1},
    "club_id": {"type": "integer", "minimum": 1},
    "category_id": {"type": "integer", "minimum": 1},
    "start_date": {"type": "string", "format": "date"},
    "end_date": {"type": "string", "format": "date"},
}


def schema(name: str, description: str, properties=None, required=None):
    return {
        "name": name,
        "description": description,
        "parameters": {
            "type": "object",
            "properties": {**FILTER_PROPERTIES, **(properties or {})},
            "required": required or [],
            "additionalProperties": False,
        },
    }


TOOL_SCHEMAS = {
    "get_overview_statistics": schema(
        "get_overview_statistics", "查询活动、社团、参与人次、活跃学生和到场率总览。"
    ),
    "get_club_ranking": schema(
        "get_club_ranking",
        "按统一活跃度查询社团排行。",
        {"metric": {"type": "string", "enum": ["activity_score"]}, "limit": {"type": "integer", "minimum": 1, "maximum": 50}},
    ),
    "get_activity_ranking": schema(
        "get_activity_ranking",
        "按参与人次查询活动排行，可使用 category_id 过滤。",
        {"metric": {"type": "string", "enum": ["participant_times"]}, "limit": {"type": "integer", "minimum": 1, "maximum": 50}},
    ),
    "get_participation_trend": schema(
        "get_participation_trend",
        "查询月度参与趋势。",
        {"granularity": {"type": "string", "enum": ["month"]}, "metric": {"type": "string", "enum": ["participant_times"]}},
    ),
    "get_distribution_statistics": schema(
        "get_distribution_statistics",
        "按类别、学院或校区查询参与分布。",
        {"dimension": {"type": "string", "enum": ["category", "college", "campus"]}, "metric": {"type": "string", "enum": ["participant_times"]}},
        ["dimension"],
    ),
    "get_student_summary": schema(
        "get_student_summary",
        "查询当前学生本人摘要；只有管理员可以指定 student_id。",
        {"student_id": {"type": "integer", "minimum": 1}},
    ),
    "get_club_summary": schema(
        "get_club_summary",
        "查询指定社团的活动、参与、到场率、活跃度和趋势摘要。",
        {"club_id": {"type": "integer", "minimum": 1}},
        ["club_id"],
    ),
}
