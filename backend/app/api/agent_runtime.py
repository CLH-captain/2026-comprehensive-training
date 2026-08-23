from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field

from app.api.dependencies import AuthenticatedUser

router = APIRouter(prefix="/agent/runtime", tags=["agent-runtime"])


class RuntimeChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=2000)


@router.get("")
def runtime_status(request: Request, user: AuthenticatedUser) -> dict:
    del user
    return request.app.state.hermes_client.status().as_dict()


@router.post("/chat")
def runtime_chat(
    payload: RuntimeChatRequest, request: Request, user: AuthenticatedUser
) -> dict[str, object]:
    del user
    return request.app.state.hermes_client.chat(payload.message).as_dict()