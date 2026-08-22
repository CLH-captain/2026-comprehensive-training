from __future__ import annotations

from typing import Any, Literal

from sqlalchemy import Connection, text

from app.statistics.filters import StatisticsFilter

DistributionDimension = Literal["category", "college", "campus"]


def category_distribution(connection: Connection, filters: StatisticsFilter) -> list[dict[str, Any]]:
    where, params = filters.activity_where(student_alias="s")
    rows = connection.execute(
        text(
            f"""
            SELECT ac.id, ac.name,
                   COUNT(DISTINCT a.id) AS activities,
                   COUNT(aa.id) AS participations,
                   COUNT(DISTINCT aa.student_id) AS students
            FROM activity_categories ac
            JOIN activities a ON a.category_id = ac.id
            JOIN venues v ON v.id = a.venue_id
            LEFT JOIN activity_attendance aa ON aa.activity_id = a.id AND aa.status IN ('present', 'late')
            LEFT JOIN students s ON s.id = aa.student_id
            WHERE {where}
            GROUP BY ac.id, ac.name
            ORDER BY participations DESC, ac.name, ac.id
            """
        ),
        params,
    ).mappings().all()
    return [dict(row) for row in rows]


def college_distribution(connection: Connection, filters: StatisticsFilter) -> list[dict[str, Any]]:
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
            """
        ),
        params,
    ).mappings().all()
    return [dict(row) for row in rows]


def campus_distribution(connection: Connection, filters: StatisticsFilter) -> list[dict[str, Any]]:
    where, params = filters.activity_where(student_alias="s")
    rows = connection.execute(
        text(
            f"""
            SELECT ca.id, ca.name,
                   COUNT(DISTINCT a.id) AS activities,
                   COUNT(aa.id) AS participations,
                   COUNT(DISTINCT aa.student_id) AS students
            FROM campuses ca
            JOIN venues v ON v.campus_id = ca.id
            JOIN activities a ON a.venue_id = v.id
            LEFT JOIN activity_attendance aa ON aa.activity_id = a.id AND aa.status IN ('present', 'late')
            LEFT JOIN students s ON s.id = aa.student_id
            WHERE {where}
            GROUP BY ca.id, ca.name
            ORDER BY participations DESC, ca.name, ca.id
            """
        ),
        params,
    ).mappings().all()
    return [dict(row) for row in rows]


def distribution(
    connection: Connection,
    filters: StatisticsFilter,
    dimension: DistributionDimension,
) -> list[dict[str, Any]]:
    functions = {
        "category": category_distribution,
        "college": college_distribution,
        "campus": campus_distribution,
    }
    return functions[dimension](connection, filters)
