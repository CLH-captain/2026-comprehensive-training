from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class StudentCreate(StrictModel):
    student_no: str = Field(min_length=3, max_length=30)
    name: str = Field(min_length=1, max_length=50)
    gender: str = Field(min_length=1, max_length=10)
    college_id: int = Field(ge=1)
    major_id: int = Field(ge=1)
    enrollment_year: int = Field(ge=2000, le=2100)
    grade_no: int = Field(ge=1, le=8)
    class_name: str = Field(min_length=1, max_length=50)
    status: Literal["active", "graduated", "suspended"] = "active"


class StudentUpdate(StrictModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    gender: str | None = Field(default=None, min_length=1, max_length=10)
    college_id: int | None = Field(default=None, ge=1)
    major_id: int | None = Field(default=None, ge=1)
    enrollment_year: int | None = Field(default=None, ge=2000, le=2100)
    grade_no: int | None = Field(default=None, ge=1, le=8)
    class_name: str | None = Field(default=None, min_length=1, max_length=50)
    status: Literal["active", "graduated", "suspended"] | None = None


class ClubCreate(StrictModel):
    code: str = Field(min_length=2, max_length=30)
    name: str = Field(min_length=2, max_length=100)
    category_id: int = Field(ge=1)
    home_campus_id: int = Field(ge=1)
    advisor_name: str | None = Field(default=None, max_length=50)
    leader_student_id: int | None = Field(default=None, ge=1)
    founded_date: date | None = None
    description: str | None = Field(default=None, max_length=5000)
    status: Literal["active", "inactive"] = "active"


class ClubUpdate(StrictModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    category_id: int | None = Field(default=None, ge=1)
    home_campus_id: int | None = Field(default=None, ge=1)
    advisor_name: str | None = Field(default=None, max_length=50)
    leader_student_id: int | None = Field(default=None, ge=1)
    founded_date: date | None = None
    description: str | None = Field(default=None, max_length=5000)
    status: Literal["active", "inactive"] | None = None


class MembershipUpsert(StrictModel):
    student_id: int = Field(ge=1)
    role: Literal["member", "core", "leader"] = "member"
    join_date: date
    status: Literal["active", "inactive"] = "active"


class ActivityCreate(StrictModel):
    code: str = Field(min_length=2, max_length=30)
    club_id: int = Field(ge=1)
    category_id: int = Field(ge=1)
    term_id: int = Field(ge=1)
    venue_id: int = Field(ge=1)
    title: str = Field(min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=10000)
    start_time: datetime
    end_time: datetime
    capacity: int = Field(ge=1, le=100000)
    status: Literal["draft", "published", "completed", "cancelled"] = "draft"

    @model_validator(mode="after")
    def validate_time(self) -> ActivityCreate:
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be earlier than end_time")
        return self


class ActivityUpdate(StrictModel):
    category_id: int | None = Field(default=None, ge=1)
    term_id: int | None = Field(default=None, ge=1)
    venue_id: int | None = Field(default=None, ge=1)
    title: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=10000)
    start_time: datetime | None = None
    end_time: datetime | None = None
    capacity: int | None = Field(default=None, ge=1, le=100000)
    status: Literal["draft", "published", "completed", "cancelled"] | None = None


class RegistrationCreate(StrictModel):
    activity_id: int = Field(ge=1)
    student_id: int = Field(ge=1)


class RegistrationStatusUpdate(StrictModel):
    status: Literal["registered", "cancelled", "waitlisted"]


class AttendanceUpsert(StrictModel):
    activity_id: int = Field(ge=1)
    student_id: int = Field(ge=1)
    status: Literal["present", "late", "absent"]
    checkin_time: datetime | None = None


class DictionaryCreate(StrictModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=255)


class CampusCreate(StrictModel):
    code: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=50)
    address: str | None = Field(default=None, max_length=255)


class CollegeCreate(StrictModel):
    code: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=100)
    primary_campus_id: int = Field(ge=1)


class MajorCreate(StrictModel):
    college_id: int = Field(ge=1)
    code: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=100)
    duration_years: int = Field(default=4, ge=1, le=8)


class TermCreate(StrictModel):
    academic_year: str = Field(min_length=4, max_length=20)
    term_no: Literal[1, 2]
    name: str = Field(min_length=1, max_length=100)
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_dates(self) -> TermCreate:
        if self.start_date >= self.end_date:
            raise ValueError("start_date must be earlier than end_date")
        return self


class VenueCreate(StrictModel):
    campus_id: int = Field(ge=1)
    code: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=100)
    venue_type: str = Field(min_length=1, max_length=30)
    capacity: int = Field(ge=1, le=100000)
