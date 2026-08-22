from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.campus import MYSQL_TABLE_ARGS
from app.models.enums import StudentStatus
from app.models.mixins import BigIntIdMixin, CreatedAtMixin


class Student(BigIntIdMixin, CreatedAtMixin, Base):
    __tablename__ = "students"
    __table_args__ = (
        CheckConstraint("grade_no BETWEEN 1 AND 8", name="grade_valid"),
        CheckConstraint(
            "status IN ('active', 'graduated', 'suspended')",
            name="status_valid",
        ),
        Index(
            "ix_students_college_major_status",
            "college_id",
            "major_id",
            "status",
        ),
        Index("ix_students_year_grade", "enrollment_year", "grade_no"),
        MYSQL_TABLE_ARGS,
    )

    student_no: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    college_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("colleges.id"), nullable=False
    )
    major_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("majors.id"), nullable=False
    )
    enrollment_year: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    grade_no: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    class_name: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default=StudentStatus.ACTIVE, server_default="active", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
