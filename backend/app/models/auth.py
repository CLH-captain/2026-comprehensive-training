from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.campus import MYSQL_TABLE_ARGS
from app.models.enums import UserRole, UserStatus
from app.models.mixins import BigIntIdMixin, CreatedAtMixin


class User(BigIntIdMixin, CreatedAtMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "role IN ('admin', 'club_manager', 'student')", name="role_valid"
        ),
        CheckConstraint("status IN ('active', 'disabled')", name="status_valid"),
        Index("ix_users_role_status", "role", "status"),
        MYSQL_TABLE_ARGS,
    )

    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(30), default=UserRole.STUDENT, server_default="student", nullable=False
    )
    student_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("students.id"), unique=True
    )
    status: Mapped[str] = mapped_column(
        String(20), default=UserStatus.ACTIVE, server_default="active", nullable=False
    )


class UserClubRole(BigIntIdMixin, Base):
    __tablename__ = "user_club_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "club_id"),
        CheckConstraint("role IN ('manager')", name="role_valid"),
        MYSQL_TABLE_ARGS,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )
    club_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("clubs.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(
        String(20), default="manager", server_default="manager", nullable=False
    )


class RevokedToken(BigIntIdMixin, Base):
    __tablename__ = "revoked_tokens"
    __table_args__ = (
        Index("ix_revoked_tokens_expires_at", "expires_at"),
        MYSQL_TABLE_ARGS,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, index=True
    )
    jti: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    revoked_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, server_default=func.now(), nullable=False
    )
