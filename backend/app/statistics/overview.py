from __future__ import annotations

from typing import Any

from sqlalchemy import Connection, text

from app.statistics.common import round_rate
from app.statistics.filters import StatisticsFilter


def _activity_count(connection: Connection, filters: StatisticsFilter) -> int:
    joins = "JOIN venues v ON v.id = a.venue_id"
    student_alias = None
    if filters.college_id is not None:
        joins += " JOIN activity_attendance aa ON aa.activity_id = a.id AND aa.status IN ('present', 'late') JOIN students s ON s.id = aa.student_id"
        student_alias = "s"
    where, params = filters.activity_where(student_alias=student_alias)
    return connection.execute(
        text(f"SELECT COUNT(DISTINCT a.id) FROM activities a {joins} WHERE {where}"),
        params,
    ).scalar_one()


def _participation_counts(connection: Connection, filters: StatisticsFilter) -> tuple[int, int]:
    where, params = filters.activity_where(student_alias="s")
    row = connection.execute(
        text(
            f"""
            SELECT COUNT(*) AS participations, COUNT(DISTINCT aa.student_id) AS active_students
            FROM activity_attendance aa
            JOIN activities a ON a.id = aa.activity_id
            JOIN venues v ON v.id = a.venue_id
            JOIN students s ON s.id = aa.student_id
            WHERE aa.status IN ('present', 'late') AND {where}
            """
        ),
        params,
    ).mappings().one()
    return row["participations"], row["active_students"]


def _registration_count(connection: Connection, filters: StatisticsFilter) -> int:
    where, params = filters.activity_where(student_alias="s")
    return connection.execute(
        text(
            f"""
            SELECT COUNT(*)
            FROM activity_registrations ar
            JOIN activities a ON a.id = ar.activity_id
            JOIN venues v ON v.id = a.venue_id
            JOIN students s ON s.id = ar.student_id
            WHERE ar.status = 'registered' AND {where}
            """
        ),
        params,
    ).scalar_one()


def overview(connection: Connection, filters: StatisticsFilter) -> dict[str, Any]:
    club_clauses = ["status = 'active'"]
    club_params: dict[str, int] = {}
    if filters.campus_id is not None:
        club_clauses.append("home_campus_id = :campus_id")
        club_params["campus_id"] = filters.campus_id
    if filters.club_id is not None:
        club_clauses.append("id = :club_id")
        club_params["club_id"] = filters.club_id
    active_clubs = connection.execute(
        text(f"SELECT COUNT(*) FROM clubs WHERE {' AND '.join(club_clauses)}"),
        club_params,
    ).scalar_one()
    completed_activities = _activity_count(connection, filters)
    participations, active_students = _participation_counts(connection, filters)
    registrations = _registration_count(connection, filters)
    attendance_rate = round_rate(100 * participations / registrations) if registrations else None
    return {
        "active_clubs": active_clubs,
        "completed_activities": completed_activities,
        "registrations": registrations,
        "participations": participations,
        "active_students": active_students,
        "attendance_rate": attendance_rate,
    }
