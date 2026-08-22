from __future__ import annotations

from typing import Any

from sqlalchemy import Connection, text

from app.statistics.common import round_rate
from app.statistics.filters import StatisticsFilter
from app.statistics.rankings import club_ranking


def student_summary(
    connection: Connection,
    student_id: int,
    filters: StatisticsFilter | None = None,
) -> dict[str, Any] | None:
    filters = filters or StatisticsFilter()
    student = connection.execute(
        text(
            """
            SELECT s.id, s.student_no, s.name, s.grade_no,
                   co.id AS college_id, co.name AS college_name,
                   m.id AS major_id, m.name AS major_name
            FROM students s
            JOIN colleges co ON co.id = s.college_id
            JOIN majors m ON m.id = s.major_id
            WHERE s.id = :student_id
            """
        ),
        {"student_id": student_id},
    ).mappings().one_or_none()
    if student is None:
        return None
    where, params = filters.activity_where(student_alias="s")
    metrics = connection.execute(
        text(
            f"""
            SELECT COUNT(aa.id) AS participations,
                   COUNT(DISTINCT a.id) AS activities,
                   COUNT(DISTINCT a.club_id) AS clubs,
                   COUNT(DISTINCT a.category_id) AS categories
            FROM students s
            LEFT JOIN activity_attendance aa ON aa.student_id = s.id AND aa.status IN ('present', 'late')
            LEFT JOIN activities a ON a.id = aa.activity_id
            LEFT JOIN venues v ON v.id = a.venue_id
            WHERE s.id = :student_id AND {where}
            """
        ),
        {**params, "student_id": student_id},
    ).mappings().one()
    registration_where, registration_params = filters.activity_where(student_alias="s")
    registrations = connection.execute(
        text(
            f"""
            SELECT COUNT(*) FROM activity_registrations ar
            JOIN students s ON s.id = ar.student_id
            JOIN activities a ON a.id = ar.activity_id
            JOIN venues v ON v.id = a.venue_id
            WHERE ar.student_id = :student_id AND ar.status = 'registered' AND {registration_where}
            """
        ),
        {**registration_params, "student_id": student_id},
    ).scalar_one()
    result = {**dict(student), **dict(metrics), "registrations": registrations}
    result["attendance_rate"] = (
        round_rate(100 * result["participations"] / registrations) if registrations else None
    )
    return result


def club_summary(
    connection: Connection,
    club_id: int,
    filters: StatisticsFilter | None = None,
) -> dict[str, Any] | None:
    club = connection.execute(
        text(
            """
            SELECT c.id, c.code, c.name, cc.name AS category_name,
                   ca.name AS campus_name, c.status
            FROM clubs c
            JOIN club_categories cc ON cc.id = c.category_id
            JOIN campuses ca ON ca.id = c.home_campus_id
            WHERE c.id = :club_id
            """
        ),
        {"club_id": club_id},
    ).mappings().one_or_none()
    if club is None:
        return None
    base_filters = filters or StatisticsFilter()
    scoped_filters = StatisticsFilter(
        term_id=base_filters.term_id,
        campus_id=base_filters.campus_id,
        college_id=base_filters.college_id,
        club_id=None,
        date_from=base_filters.date_from,
        date_to=base_filters.date_to,
    )
    ranking_rows = club_ranking(connection, scoped_filters, limit=100)
    metrics = next((row for row in ranking_rows if row["id"] == club_id), None)
    if metrics is None:
        metrics = {
            "activities": 0,
            "participations": 0,
            "students": 0,
            "activity_score": 0.0,
        }
    members = connection.execute(
        text(
            "SELECT COUNT(*) FROM club_memberships WHERE club_id = :club_id AND status = 'active'"
        ),
        {"club_id": club_id},
    ).scalar_one()
    return {**dict(club), **metrics, "members": members}
