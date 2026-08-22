from datetime import date

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import BigIntIdMixin

MYSQL_TABLE_ARGS = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}


class Campus(BigIntIdMixin, Base):
    __tablename__ = "campuses"
    __table_args__ = MYSQL_TABLE_ARGS

    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    address: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("1"), nullable=False
    )


class AcademicTerm(BigIntIdMixin, Base):
    __tablename__ = "academic_terms"
    __table_args__ = (
        UniqueConstraint("academic_year", "term_no"),
        CheckConstraint("term_no IN (1, 2)", name="term_no_valid"),
        CheckConstraint("start_date < end_date", name="date_order_valid"),
        MYSQL_TABLE_ARGS,
    )

    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)
    term_no: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_default: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("0"), nullable=False, index=True
    )


class College(BigIntIdMixin, Base):
    __tablename__ = "colleges"
    __table_args__ = MYSQL_TABLE_ARGS

    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    primary_campus_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("campuses.id"), nullable=False, index=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("1"), nullable=False
    )


class Major(BigIntIdMixin, Base):
    __tablename__ = "majors"
    __table_args__ = (
        CheckConstraint("duration_years BETWEEN 1 AND 8", name="duration_valid"),
        Index("ix_majors_college_active", "college_id", "is_active"),
        MYSQL_TABLE_ARGS,
    )

    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    college_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("colleges.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    duration_years: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("1"), nullable=False
    )


class Venue(BigIntIdMixin, Base):
    __tablename__ = "venues"
    __table_args__ = (
        CheckConstraint("capacity > 0", name="capacity_positive"),
        Index("ix_venues_campus_active", "campus_id", "is_active"),
        MYSQL_TABLE_ARGS,
    )

    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    campus_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("campuses.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    venue_type: Mapped[str] = mapped_column(String(30), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("1"), nullable=False
    )
