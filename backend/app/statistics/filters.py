from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Any


def _as_datetime(value: date | datetime | None) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return value
    return datetime.combine(value, time.min)


@dataclass(frozen=True, slots=True)
class StatisticsFilter:
    term_id: int | None = None
    campus_id: int | None = None
    college_id: int | None = None
    club_id: int | None = None
    activity_category_id: int | None = None
    date_from: date | datetime | None = None
    date_to: date | datetime | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "term_id",
            "campus_id",
            "college_id",
            "club_id",
            "activity_category_id",
        ):
            value = getattr(self, field_name)
            if value is not None and value < 1:
                raise ValueError(f"{field_name} must be positive")
        start = _as_datetime(self.date_from)
        end = _as_datetime(self.date_to)
        if start is not None and end is not None and start >= end:
            raise ValueError("date_from must be earlier than date_to")

    @property
    def start_datetime(self) -> datetime | None:
        return _as_datetime(self.date_from)

    @property
    def end_datetime(self) -> datetime | None:
        return _as_datetime(self.date_to)

    def activity_where(
        self,
        *,
        activity_alias: str = "a",
        venue_alias: str = "v",
        student_alias: str | None = None,
        completed_only: bool = True,
    ) -> tuple[str, dict[str, Any]]:
        clauses = ["1 = 1"]
        params: dict[str, Any] = {}
        if completed_only:
            clauses.append(f"{activity_alias}.status = 'completed'")
        fields = (
            ("term_id", self.term_id, f"{activity_alias}.term_id = :term_id"),
            ("campus_id", self.campus_id, f"{venue_alias}.campus_id = :campus_id"),
            ("club_id", self.club_id, f"{activity_alias}.club_id = :club_id"),
            (
                "activity_category_id",
                self.activity_category_id,
                f"{activity_alias}.category_id = :activity_category_id",
            ),
        )
        for name, value, clause in fields:
            if value is not None:
                clauses.append(clause)
                params[name] = value
        if self.college_id is not None:
            if student_alias is None:
                raise ValueError("college_id filtering requires a student alias")
            clauses.append(f"{student_alias}.college_id = :college_id")
            params["college_id"] = self.college_id
        if self.start_datetime is not None:
            clauses.append(f"{activity_alias}.start_time >= :date_from")
            params["date_from"] = self.start_datetime
        if self.end_datetime is not None:
            clauses.append(f"{activity_alias}.start_time < :date_to")
            params["date_to"] = self.end_datetime
        return " AND ".join(clauses), params
