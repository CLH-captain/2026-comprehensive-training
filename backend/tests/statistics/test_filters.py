from datetime import date, datetime, time

import pytest

from app.statistics.common import fill_months, month_range, round_rate
from app.statistics.filters import StatisticsFilter


def test_activity_filter_uses_venue_campus_and_half_open_dates() -> None:
    filters = StatisticsFilter(
        term_id=2,
        campus_id=1,
        club_id=4,
        date_from=date(2026, 3, 1),
        date_to=date(2026, 4, 1),
    )

    where, params = filters.activity_where()

    assert "a.status = 'completed'" in where
    assert "a.term_id = :term_id" in where
    assert "v.campus_id = :campus_id" in where
    assert "a.club_id = :club_id" in where
    assert "a.start_time >= :date_from" in where
    assert "a.start_time < :date_to" in where
    assert params["date_from"] == datetime.combine(date(2026, 3, 1), time.min)
    assert params["date_to"] == datetime.combine(date(2026, 4, 1), time.min)


def test_college_filter_requires_student_join_alias() -> None:
    filters = StatisticsFilter(college_id=3)

    with pytest.raises(ValueError, match="student alias"):
        filters.activity_where()

    where, params = filters.activity_where(student_alias="s")
    assert "s.college_id = :college_id" in where
    assert params["college_id"] == 3


def test_invalid_filter_range_is_rejected() -> None:
    with pytest.raises(ValueError, match="earlier"):
        StatisticsFilter(date_from=date(2026, 4, 1), date_to=date(2026, 4, 1))


def test_month_range_is_left_closed_and_right_open() -> None:
    assert month_range(date(2025, 11, 1), date(2026, 3, 1)) == [
        "2025-11",
        "2025-12",
        "2026-01",
        "2026-02",
    ]


def test_fill_months_adds_zero_rows() -> None:
    result = fill_months(
        [{"month": "2026-01", "activities": 2, "participations": 8}],
        start=date(2025, 12, 1),
        end=date(2026, 3, 1),
        value_fields=("activities", "participations"),
    )

    assert result == [
        {"month": "2025-12", "activities": 0, "participations": 0},
        {"month": "2026-01", "activities": 2, "participations": 8},
        {"month": "2026-02", "activities": 0, "participations": 0},
    ]


def test_round_rate_uses_two_decimal_places() -> None:
    assert round_rate("81.235") == 81.24
    assert round_rate(None) is None
