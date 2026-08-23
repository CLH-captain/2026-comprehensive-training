from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictAgentModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class AgentContext(StrictAgentModel):
    term_id: int | None = Field(default=None, ge=1)
    campus_id: int | None = Field(default=None, ge=1)


class AgentChatRequest(StrictAgentModel):
    message: str = Field(min_length=1, max_length=2000)
    conversation_id: int | None = Field(default=None, ge=1)
    context: AgentContext = Field(default_factory=AgentContext)


class AgentToolCallView(BaseModel):
    name: str
    arguments: dict[str, Any]
    success: bool
    error: str | None = None


class AgentChartSeries(BaseModel):
    name: str
    data: list[Any]


class AgentVisualization(BaseModel):
    type: Literal["bar", "line", "pie"]
    title: str
    categories: list[str] = Field(default_factory=list)
    series: list[AgentChartSeries]


class AgentChatResponse(BaseModel):
    conversation_id: int
    answer: str
    model_used: str
    fallback_used: bool = False
    tool_calls: list[AgentToolCallView]
    data: Any | None = None
    visualization: AgentVisualization | None = None


class ConversationSummary(BaseModel):
    id: int
    title: str
    message_count: int
    created_at: datetime
    updated_at: datetime


class AgentMessageView(BaseModel):
    id: int
    role: Literal["user", "assistant"]
    content: str
    model_used: str | None
    tool_calls: list[AgentToolCallView]
    created_at: datetime
