import logging
from typing import Annotated

from fastapi import APIRouter, Path, Request

from app.agent.fallback import allows_fallback, is_recoverable_local_error
from app.api.dependencies import AuthenticatedUser
from app.core.errors import AppError
from app.core.security import create_agent_context_token
from app.schemas.agent import (
    AgentChatRequest,
    AgentChatResponse,
    AgentMessageView,
    ConversationSummary,
)
from app.services.agent import (
    AgentService,
    reply_data,
    reply_visualization,
    tool_call_views,
)
from app.statistics.filters import StatisticsFilter
from app.statistics.service import StatisticsService

router = APIRouter(prefix="/agent", tags=["agent"])


@router.get("/conversations", response_model=list[ConversationSummary])
def list_conversations(request: Request, user: AuthenticatedUser) -> list[dict]:
    with request.app.state.engine.connect() as connection:
        return AgentService(connection).list_conversations(user.id)


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[AgentMessageView],
)
def list_messages(
    conversation_id: Annotated[int, Path(ge=1)],
    request: Request,
    user: AuthenticatedUser,
) -> list[dict]:
    with request.app.state.engine.connect() as connection:
        return AgentService(connection).list_messages(user.id, conversation_id)


@router.delete("/conversations/{conversation_id}", status_code=204)
def delete_conversation(
    conversation_id: Annotated[int, Path(ge=1)],
    request: Request,
    user: AuthenticatedUser,
) -> None:
    with request.app.state.engine.begin() as connection:
        AgentService(connection).delete_conversation(user.id, conversation_id)


def _aggregate_snapshot(request: Request, payload: AgentChatRequest) -> dict:
    filters = StatisticsFilter(
        term_id=payload.context.term_id,
        campus_id=payload.context.campus_id,
    )
    with request.app.state.engine.connect() as connection:
        return StatisticsService(connection).dashboard(filters)


def _agent_reply(
    request: Request,
    payload: AgentChatRequest,
    user: AuthenticatedUser,
    prompt: str,
    context_token: str,
):
    try:
        return request.app.state.hermes_client.chat(prompt, context_token)
    except AppError as first_error:
        if not is_recoverable_local_error(first_error):
            raise
    try:
        return request.app.state.hermes_client.chat(prompt, context_token)
    except AppError as second_error:
        if not is_recoverable_local_error(second_error):
            raise
        if not allows_fallback(user.role, payload.message):
            raise
        return request.app.state.deepseek_client.chat(
            question=payload.message,
            snapshot=_aggregate_snapshot(request, payload),
        )


@router.post("/chat", response_model=AgentChatResponse)
def chat(payload: AgentChatRequest, request: Request, user: AuthenticatedUser) -> dict:
    with request.app.state.engine.begin() as connection:
        pending = AgentService(connection).begin_chat(
            user_id=user.id,
            message=payload.message,
            conversation_id=payload.conversation_id,
            term_id=payload.context.term_id,
            campus_id=payload.context.campus_id,
        )
    context_token = create_agent_context_token(
        user_id=user.id,
        conversation_id=pending.conversation_id,
        secret=request.app.state.settings.jwt_secret,
    )
    reply = _agent_reply(request, payload, user, pending.prompt, context_token)
    with request.app.state.engine.begin() as connection:
        AgentService(connection).complete_chat(pending.conversation_id, reply)
    logging.getLogger("szut.agent").info(
        "agent.completed",
        extra={
            "request_id": request.state.request_id,
            "source": reply.adapter,
            "model": reply.model,
            "fallback": reply.adapter == "deepseek_fallback",
        },
    )
    return {
        "conversation_id": pending.conversation_id,
        "answer": reply.content,
        "model_used": reply.model,
        "fallback_used": reply.adapter == "deepseek_fallback",
        "tool_calls": tool_call_views(reply.tool_calls),
        "data": reply_data(reply),
        "visualization": reply_visualization(reply),
    }
