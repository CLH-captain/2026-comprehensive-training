from __future__ import annotations

from typing import Any, Literal

from sqlalchemy import Connection, text

from app.statistics.common import round_rate
from app.statistics.filters import StatisticsFilter

RankingDimension = Literal["club", "activity", "student", "college"]


def _limit(value: int) -> int:
    if not 1 <= value <= 100:
        raise ValueError("limit must be between 1 and 100")
    return value


def club_ranking(
    connection: Connection,
    filters: StatisticsFilter,
    limit: int = 10,
) -> list[dict[str, Any]]:
    limit = _limit(limit)
    where, params = filters.activity_where(student_alias="s")
    rows = connection.execute(
        text(
            f"""
            SELECT c.id, c.name,
                   COUNT(DISTINCT a.id) AS activities,
                   COUNT(aa.id) AS participations,
                   COUNT(DISTINCT aa.student_id) AS students
            FROM clubs c
            JOIN activities a ON a.club_id = c.id
            JOIN venues v ON v.id = a.venue_id
            LEFT JOIN activity_attendance aa ON aa.activity_id = a.id AND aa.status IN ('present', 'late')
            LEFT JOIN students s ON s.id = aa.student_id
            WHERE c.status = 'active' AND {where}
            GROUP BY c.id, c.name
            """
        ),
        params,
    ).mappings().all()
    values = [dict(row) for row in rows]
    maxima = {
        key: max((row[key] for row in values), default=0)
        for key in ("activities", "participations", "students")
    }
    for row in values:
        activity_score = row["activities"] / maxima["activities"] * 100 if maxima["activities"] else 0
        participation_score = row["participations"] / maxima["participations"] * 100 if maxima["participations"] else 0
        student_score = row["students"] / maxima["students"] * 100 if maxima["students"] else 0
        row["activity_score"] = round_rate(
            0.5 * activity_score + 0.3 * participation_score + 0.2 * student_score
        )
    values.sort(key=lambda row: (-row["activity_score"], row["name"], row["id"]))
    return values[:limit]


def activity_ranking(
    connection: Connection,
    filters: StatisticsFilter,
    limit: int = 10,
) -> list[dict[str, Any]]:
    limit = _limit(limit)
    student_alias = "s" if filters.college_id is not None else None
    college_join = ""
    if student_alias:
        college_join = "JOIN activity_attendance filter_aa ON filter_aa.activity_id = a.id AND filter_aa.status IN ('present', 'late') JOIN students s ON s.id = filter_aa.student_id"
    where, params = filters.activity_where(student_alias=student_alias)
    rows = connection.execute(
        text(
            f"""
            SELECT a.id, a.title, c.name AS club_name, a.start_time, a.capacity,
                   (SELECT COUNT(*) FROM activity_registrations ar
                    WHERE ar.activity_id = a.id AND ar.status = 'registered') AS registrations,
                   (SELECT COUNT(*) FROM activity_attendance aa
                    WHERE aa.activity_id = a.id AND aa.status IN ('present', 'late')) AS attendance
            FROM activities a
            JOIN clubs c ON c.id = a.club_id
            JOIN venues v ON v.id = a.venue_id
            {college_join}
            WHERE {where}
            GROUP BY a.id, a.title, c.name, a.start_time, a.capacity
            ORDER BY attendance DESC, a.title, a.id
            LIMIT :limit
            """
        ),
        {**params, "limit": limit},
    ).mappings().all()
    values = []
    for raw in rows:
        row = dict(raw)
        row["attendance_rate"] = (
            round_rate(100 * row["attendance"] / row["registrations"])
            if row["registrations"]
            else None
        )
        values.append(row)
    return values


def student_ranking(
    connection: Connection,
    filters: StatisticsFilter,
    limit: int = 10,
) -> list[dict[str, Any]]:
    limit = _limit(limit)
    where, params = filters.activity_where(student_alias="s")
    rows = connection.execute(
        text(
            f"""
            SELECT s.id, s.student_no, s.name, co.name AS college_name,
                   COUNT(aa.id) AS participations,
                   COUNT(DISTINCT a.club_id) AS clubs,
                   COUNT(DISTINCT a.category_id) AS categories
            FROM students s
            JOIN colleges co ON co.id = s.college_id
            JOIN activity_attendance aa ON aa.student_id = s.id AND aa.status IN ('present', 'late')
            JOIN activities a ON a.id = aa.activity_id
            JOIN venues v ON v.id = a.venue_id
            WHERE {where}
            GROUP BY s.id, s.student_no, s.name, co.name
            ORDER BY participations DESC, s.name, s.id
            LIMIT :limit
            """
        ),
        {**params, "limit": limit},
    ).mappings().all()
    return [dict(row) for row in rows]


def college_ranking(
    connection: Connection,
    filters: StatisticsFilter,
    limit: int = 10,
) -> list[dict[str, Any]]:
    limit = _limit(limit)
    where, params = filters.activity_where(student_alias="s")
    rows = connection.execute(
        text(
            f"""
            SELECT co.id, co.name,
                   COUNT(aa.id) AS participations,
                   COUNT(DISTINCT aa.student_id) AS students,
                   COUNT(DISTINCT a.id) AS activities
            FROM colleges co
            JOIN students s ON s.college_id = co.id
            JOIN activity_attendance aa ON aa.student_id = s.id AND aa.status IN ('present', 'late')
            JOIN activities a ON a.id = aa.activity_id
            JOIN venues v ON v.id = a.venue_id
            WHERE {where}
            GROUP BY co.id, co.name
            ORDER BY participations DESC, co.name, co.id
            LIMIT :limit
            """
        ),
        {**params, "limit": limit},
    ).mappings().all()
    return [dict(row) for row in rows]


def ranking(
    connection: Connection,
    filters: StatisticsFilter,
    dimension: RankingDimension,
    limit: int = 10,
) -> list[dict[str, Any]]:
    functions = {
        "club": club_ranking,
        "activity": activity_ranking,
        "student": student_ranking,
        "college": college_ranking,
    }
    return functions[dimension](connection, filters, limit)
