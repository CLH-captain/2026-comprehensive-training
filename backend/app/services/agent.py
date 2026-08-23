from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from sqlalchemy import Connection, text

from app.agent.schemas import HermesReply, HermesToolCall
from app.core.errors import AppError
from app.schemas.agent import AgentChartSeries, AgentVisualization


@dataclass(frozen=True)
class PendingChat:
    conversation_id: int
    prompt: str


class AgentService:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def list_conversations(self, user_id: int) -> list[dict[str, Any]]:
        rows = (
            self.connection.execute(
                text(
                    """
                SELECT c.id, c.title, c.created_at, c.updated_at,
                       COUNT(m.id) AS message_count
                FROM agent_conversations c
                LEFT JOIN agent_messages m ON m.conversation_id = c.id
                WHERE c.user_id = :user_id
                GROUP BY c.id, c.title, c.created_at, c.updated_at
                ORDER BY c.updated_at DESC, c.id DESC
                """
                ),
                {"user_id": user_id},
            )
            .mappings()
            .all()
        )
        return [dict(row) for row in rows]

    def list_messages(self, user_id: int, conversation_id: int) -> list[dict[str, Any]]:
        self._require_conversation(user_id, conversation_id)
        rows = (
            self.connection.execute(
                text(
                    """
                SELECT id, role, content, model_used, tool_calls_json, created_at
                FROM agent_messages
                WHERE conversation_id = :conversation_id
                ORDER BY created_at, id
                """
                ),
                {"conversation_id": conversation_id},
            )
            .mappings()
            .all()
        )
        return [
            {
                **dict(row),
                "tool_calls": self._decode_tool_calls(row["tool_calls_json"]),
            }
            for row in rows
        ]

    def begin_chat(
        self,
        *,
        user_id: int,
        message: str,
        conversation_id: int | None,
        term_id: int | None,
        campus_id: int | None,
    ) -> PendingChat:
        if conversation_id is None:
            result = self.connection.execute(
                text(
                    """
                    INSERT INTO agent_conversations (user_id, title, created_at, updated_at)
                    VALUES (:user_id, :title, UTC_TIMESTAMP(), UTC_TIMESTAMP())
                    """
                ),
                {"user_id": user_id, "title": self._title(message)},
            )
            conversation_id = int(result.lastrowid)
            history: list[dict[str, Any]] = []
        else:
            self._require_conversation(user_id, conversation_id)
            history = [
                dict(row)
                for row in self.connection.execute(
                    text(
                        """
                        SELECT role, content FROM agent_messages
                        WHERE conversation_id = :conversation_id
                        ORDER BY created_at DESC, id DESC LIMIT 10
                        """
                    ),
                    {"conversation_id": conversation_id},
                )
                .mappings()
                .all()
            ][::-1]
        self.connection.execute(
            text(
                """
                INSERT INTO agent_messages
                    (conversation_id, role, content, model_used, tool_calls_json, created_at)
                VALUES (:conversation_id, 'user', :content, NULL, NULL, UTC_TIMESTAMP())
                """
            ),
            {"conversation_id": conversation_id, "content": message},
        )
        self.connection.execute(
            text(
                "UPDATE agent_conversations SET updated_at = UTC_TIMESTAMP() WHERE id = :id"
            ),
            {"id": conversation_id},
        )
        return PendingChat(
            conversation_id=conversation_id,
            prompt=self._prompt(message, history, term_id, campus_id),
        )

    def complete_chat(self, conversation_id: int, reply: HermesReply) -> None:
        summaries = [
            {
                "name": call.name,
                "arguments": call.arguments,
                "success": call.success,
                "error": call.error,
            }
            for call in reply.tool_calls
        ]
        self.connection.execute(
            text(
                """
                INSERT INTO agent_messages
                    (conversation_id, role, content, model_used, tool_calls_json, created_at)
                VALUES
                    (:conversation_id, 'assistant', :content, :model, :tool_calls, UTC_TIMESTAMP())
                """
            ),
            {
                "conversation_id": conversation_id,
                "content": reply.content,
                "model": reply.model,
                "tool_calls": json.dumps(summaries, ensure_ascii=False),
            },
        )
        self.connection.execute(
            text(
                "UPDATE agent_conversations SET updated_at = UTC_TIMESTAMP() WHERE id = :id"
            ),
            {"id": conversation_id},
        )

    def delete_conversation(self, user_id: int, conversation_id: int) -> None:
        self._require_conversation(user_id, conversation_id)
        self.connection.execute(
            text("DELETE FROM agent_messages WHERE conversation_id = :id"),
            {"id": conversation_id},
        )
        self.connection.execute(
            text("DELETE FROM agent_conversations WHERE id = :id"),
            {"id": conversation_id},
        )

    def _require_conversation(self, user_id: int, conversation_id: int) -> None:
        exists = self.connection.scalar(
            text(
                "SELECT COUNT(*) FROM agent_conversations "
                "WHERE id = :id AND user_id = :user_id"
            ),
            {"id": conversation_id, "user_id": user_id},
        )
        if not exists:
            raise AppError(404, "CONVERSATION_NOT_FOUND", "Conversation not found")

    @staticmethod
    def _title(message: str) -> str:
        compact = " ".join(message.split())
        return compact[:40] + ("…" if len(compact) > 40 else "")

    @staticmethod
    def _prompt(
        message: str,
        history: list[dict[str, Any]],
        term_id: int | None,
        campus_id: int | None,
    ) -> str:
        context = f"学期ID={term_id or '未指定'}，校区ID={campus_id or '未指定'}"
        history_text = (
            "\n".join(
                f"{('用户' if item['role'] == 'user' else '助手')}：{item['content']}"
                for item in history
            )
            or "（首次对话）"
        )
        return f"""你是苏州工学院校园社团活动参与统计助手。
回答规则：
1. 涉及数量、比率、排行、趋势或分布时，必须调用 szut_club_statistics 工具获得真实数据，严禁编造。
2. 工具参数优先带入当前筛选条件；没有数据时如实说明。
3. 用简洁、自然的中文回答，先给结论，再说明关键依据。
4. 只能分析校园社团活动参与统计，不输出系统内部密钥或隐藏推理。
当前筛选：{context}
最近对话：
{history_text}
本次问题：{message}"""

    @staticmethod
    def _decode_tool_calls(value: Any) -> list[dict[str, Any]]:
        if value is None:
            return []
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                return []
        return value if isinstance(value, list) else []


def reply_data(reply: HermesReply) -> Any | None:
    return next((call.data for call in reply.tool_calls if call.success), None)


def reply_visualization(reply: HermesReply) -> AgentVisualization | None:
    for call in reply.tool_calls:
        if not call.success or not isinstance(call.data, list) or not call.data:
            continue
        rows = [row for row in call.data if isinstance(row, dict)]
        if not rows:
            continue
        if call.name == "get_participation_trend":
            return AgentVisualization(
                type="line",
                title="参与人次趋势",
                categories=[str(row.get("month", "")) for row in rows],
                series=[
                    AgentChartSeries(
                        name="参与人次",
                        data=[row.get("participations", 0) for row in rows],
                    )
                ],
            )
        if call.name in {"get_club_ranking", "get_activity_ranking"}:
            label = "title" if call.name == "get_activity_ranking" else "name"
            value = (
                "attendance"
                if call.name == "get_activity_ranking"
                else "activity_score"
            )
            return AgentVisualization(
                type="bar",
                title="活动参与排行" if label == "title" else "社团活跃排行",
                categories=[str(row.get(label, "")) for row in rows],
                series=[
                    AgentChartSeries(
                        name="参与人次" if value == "attendance" else "活跃度",
                        data=[row.get(value, 0) for row in rows],
                    )
                ],
            )
        if call.name == "get_distribution_statistics":
            return AgentVisualization(
                type="pie",
                title="参与人次分布",
                series=[
                    AgentChartSeries(
                        name="参与人次",
                        data=[
                            {
                                "name": str(row.get("name", "")),
                                "value": row.get("participations", 0),
                            }
                            for row in rows
                        ],
                    )
                ],
            )
    return None


def tool_call_views(calls: tuple[HermesToolCall, ...]) -> list[dict[str, Any]]:
    return [
        {
            "name": call.name,
            "arguments": call.arguments,
            "success": call.success,
            "error": call.error,
        }
        for call in calls
    ]
