from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import Connection, text

from app.statistics.common import fill_months
from app.statistics.filters import StatisticsFilter


def _period(connection: Connection, filters: StatisticsFilter) -> tuple[date | datetime, date | datetime]:
    if filters.start_datetime is not None and filters.end_datetime is not None:
        return filters.start_datetime, filters.end_datetime
    if filters.term_id is not None:
        row = connection.execute(
            text("SELECT start_date, end_date FROM academic_terms WHERE id = :term_id"),
            {"term_id": filters.term_id},
        ).mappings().one()
        return row["start_date"], row["end_date"] + timedelta(days=1)
    row = connection.execute(
        text("SELECT MIN(start_time) AS start_time, MAX(start_time) AS end_time FROM activities")
    ).mappings().one()
    end = row["end_time"]
    return row["start_time"], date(end.year + (end.month == 12), end.month % 12 + 1, 1)


def monthly_trend(connection: Connection, filters: StatisticsFilter) -> list[dict[str, Any]]:
    student_join = "LEFT JOIN activity_attendance aa ON aa.activity_id = a.id AND aa.status IN ('present', 'late') LEFT JOIN students s ON s.id = aa.student_id"
    if filters.college_id is not None:
        student_join = "JOIN activity_attendance aa ON aa.activity_id = a.id AND aa.status IN ('present', 'late') JOIN students s ON s.id = aa.student_id"
    where, params = filters.activity_where(student_alias="s")
    rows = connection.execute(
        text(
            f"""
            SELECT DATE_FORMAT(a.start_time, '%Y-%m') AS month,
                   COUNT(DISTINCT a.id) AS activities,
                   COUNT(aa.id) AS participations,
                   COUNT(DISTINCT aa.student_id) AS active_students
            FROM activities a
            JOIN venues v ON v.id = a.venue_id
            {student_join}
            WHERE {where}
            GROUP BY DATE_FORMAT(a.start_time, '%Y-%m')
            ORDER BY month
            """
        ),
        params,
    ).mappings().all()
    start, end = _period(connection, filters)
    return fill_months(
        [dict(row) for row in rows],
        start=start,
        end=end,
        value_fields=("activities", "participations", "active_students"),
    )
