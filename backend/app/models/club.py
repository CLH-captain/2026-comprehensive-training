from datetime import date

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.campus import MYSQL_TABLE_ARGS
from app.models.enums import ClubStatus, MembershipRole, MembershipStatus
from app.models.mixins import BigIntIdMixin


class ClubCategory(BigIntIdMixin, Base):
    __tablename__ = "club_categories"
    __table_args__ = MYSQL_TABLE_ARGS

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("1"), nullable=False
    )


class Club(BigIntIdMixin, Base):
    __tablename__ = "clubs"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'inactive')", name="status_valid"),
        Index("ix_clubs_category_campus_status", "category_id", "home_campus_id", "status"),
        MYSQL_TABLE_ARGS,
    )

    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("club_categories.id"), nullable=False
    )
    home_campus_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("campuses.id"), nullable=False
    )
    advisor_name: Mapped[str | None] = mapped_column(String(50))
    leader_student_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("students.id")
    )
    founded_date: Mapped[date | None] = mapped_column(Date)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(20), default=ClubStatus.ACTIVE, server_default="active", nullable=False
    )


class ClubMembership(BigIntIdMixin, Base):
    __tablename__ = "club_memberships"
    __table_args__ = (
        UniqueConstraint("club_id", "student_id"),
        CheckConstraint("role IN ('member', 'core', 'leader')", name="role_valid"),
        CheckConstraint("status IN ('active', 'inactive')", name="status_valid"),
        Index("ix_memberships_student_status", "student_id", "status"),
        Index("ix_memberships_club_status", "club_id", "status"),
        MYSQL_TABLE_ARGS,
    )

    club_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("clubs.id"), nullable=False
    )
    student_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("students.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(
        String(20), default=MembershipRole.MEMBER, server_default="member", nullable=False
    )
    join_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default=MembershipStatus.ACTIVE,
        server_default="active",
        nullable=False,
    )
