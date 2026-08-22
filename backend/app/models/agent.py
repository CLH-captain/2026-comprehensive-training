from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.campus import MYSQL_TABLE_ARGS
from app.models.enums import MessageRole
from app.models.mixins import BigIntIdMixin, CreatedAtMixin


class AgentConversation(BigIntIdMixin, CreatedAtMixin, Base):
    __tablename__ = "agent_conversations"
    __table_args__ = (
        Index("ix_agent_conversations_user_updated", "user_id", "updated_at"),
        MYSQL_TABLE_ARGS,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        server_default=func.now(),
        onupdate=datetime.now,
        nullable=False,
    )


class AgentMessage(BigIntIdMixin, CreatedAtMixin, Base):
    __tablename__ = "agent_messages"
    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant')", name="role_valid"),
        Index("ix_agent_messages_conversation_created", "conversation_id", "created_at"),
        MYSQL_TABLE_ARGS,
    )

    conversation_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("agent_conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    model_used: Mapped[str | None] = mapped_column(String(100))
    tool_calls_json: Mapped[dict[str, object] | list[object] | None] = mapped_column(JSON)

    def __init__(self, **kwargs: object) -> None:
        if "role" not in kwargs:
            kwargs["role"] = MessageRole.USER
        super().__init__(**kwargs)
