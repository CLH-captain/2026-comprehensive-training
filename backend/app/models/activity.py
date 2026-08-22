from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.campus import MYSQL_TABLE_ARGS
from app.models.enums import (
    ActivityStatus,
    AttendanceStatus,
    RegistrationSource,
    RegistrationStatus,
)
from app.models.mixins import BigIntIdMixin, CreatedAtMixin


class ActivityCategory(BigIntIdMixin, Base):
    __tablename__ = "activity_categories"
    __table_args__ = MYSQL_TABLE_ARGS

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("1"), nullable=False
    )


class Activity(BigIntIdMixin, CreatedAtMixin, Base):
    __tablename__ = "activities"
    __table_args__ = (
        CheckConstraint("start_time < end_time", name="time_order_valid"),
        CheckConstraint("capacity > 0", name="capacity_positive"),
        CheckConstraint(
            "status IN ('draft', 'published', 'completed', 'cancelled')",
            name="status_valid",
        ),
        Index("ix_activities_term_status_start", "term_id", "status", "start_time"),
        Index("ix_activities_club_status", "club_id", "status"),
        Index("ix_activities_venue_start", "venue_id", "start_time"),
        MYSQL_TABLE_ARGS,
    )

    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    club_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("clubs.id"), nullable=False
    )
    category_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("activity_categories.id"), nullable=False
    )
    term_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("academic_terms.id"), nullable=False
    )
    venue_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("venues.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default=ActivityStatus.DRAFT, server_default="draft", nullable=False
    )


class ActivityRegistration(BigIntIdMixin, Base):
    __tablename__ = "activity_registrations"
    __table_args__ = (
        UniqueConstraint("activity_id", "student_id"),
        CheckConstraint(
            "status IN ('registered', 'cancelled', 'waitlisted')",
            name="status_valid",
        ),
        CheckConstraint("source IN ('web', 'import', 'generated')", name="source_valid"),
        Index("ix_registrations_activity_status", "activity_id", "status"),
        Index("ix_registrations_student_status", "student_id", "status"),
        MYSQL_TABLE_ARGS,
    )

    activity_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("activities.id"), nullable=False
    )
    student_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("students.id"), nullable=False
    )
    register_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default=RegistrationStatus.REGISTERED,
        server_default="registered",
        nullable=False,
    )
    source: Mapped[str] = mapped_column(
        String(20), default=RegistrationSource.WEB, server_default="web", nullable=False
    )


class ActivityAttendance(BigIntIdMixin, Base):
    __tablename__ = "activity_attendance"
    __table_args__ = (
        UniqueConstraint("activity_id", "student_id"),
        CheckConstraint("status IN ('present', 'late', 'absent')", name="status_valid"),
        Index("ix_attendance_activity_status", "activity_id", "status"),
        Index("ix_attendance_student_status", "student_id", "status"),
        MYSQL_TABLE_ARGS,
    )

    activity_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("activities.id"), nullable=False
    )
    student_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("students.id"), nullable=False
    )
    registration_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("activity_registrations.id")
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default=AttendanceStatus.ABSENT,
        server_default="absent",
        nullable=False,
    )
    checkin_time: Mapped[datetime | None] = mapped_column(DateTime)
