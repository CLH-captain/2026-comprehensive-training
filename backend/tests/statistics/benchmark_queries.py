from __future__ import annotations

from typing import Any

from sqlalchemy import Connection, text


def benchmark_overview(connection: Connection) -> dict[str, Any]:
    row = connection.execute(
        text(
            """
            SELECT
                (SELECT COUNT(*) FROM clubs WHERE status = 'active') AS active_clubs,
                (SELECT COUNT(*) FROM activities WHERE status = 'completed') AS completed_activities,
                (SELECT COUNT(*) FROM activity_registrations ar JOIN activities a ON a.id = ar.activity_id
                 WHERE ar.status = 'registered' AND a.status = 'completed') AS registrations,
                (SELECT COUNT(*) FROM activity_attendance aa JOIN activities a ON a.id = aa.activity_id
                 WHERE aa.status IN ('present', 'late') AND a.status = 'completed') AS participations,
                (SELECT COUNT(DISTINCT aa.student_id) FROM activity_attendance aa
                 JOIN activities a ON a.id = aa.activity_id
                 WHERE aa.status IN ('present', 'late') AND a.status = 'completed') AS active_students
            """
        )
    ).mappings().one()
    result = dict(row)
    result["attendance_rate"] = round(100 * result["participations"] / result["registrations"], 2)
    return result


def benchmark_monthly(connection: Connection) -> list[dict[str, Any]]:
    rows = connection.execute(
        text(
            """
            SELECT DATE_FORMAT(a.start_time, '%Y-%m') AS month,
                   COUNT(DISTINCT a.id) AS activities,
                   COUNT(aa.id) AS participations,
                   COUNT(DISTINCT aa.student_id) AS active_students
            FROM activities a
            LEFT JOIN activity_attendance aa
              ON aa.activity_id = a.id AND aa.status IN ('present', 'late')
            WHERE a.status = 'completed'
            GROUP BY DATE_FORMAT(a.start_time, '%Y-%m')
            ORDER BY month
            """
        )
    ).mappings().all()
    return [dict(row) for row in rows]


def benchmark_club_ranking(connection: Connection, limit: int) -> list[dict[str, Any]]:
    rows = connection.execute(
        text(
            """
            WITH metrics AS (
                SELECT c.id, c.name, COUNT(DISTINCT a.id) AS activities,
                       COUNT(aa.id) AS participations,
                       COUNT(DISTINCT aa.student_id) AS students
                FROM clubs c
                JOIN activities a ON a.club_id = c.id AND a.status = 'completed'
                LEFT JOIN activity_attendance aa
                  ON aa.activity_id = a.id AND aa.status IN ('present', 'late')
                WHERE c.status = 'active'
                GROUP BY c.id, c.name
            ), maxima AS (
                SELECT MAX(activities) AS max_activities,
                       MAX(participations) AS max_participations,
                       MAX(students) AS max_students
                FROM metrics
            )
            SELECT m.id, m.activities, m.participations, m.students,
                   ROUND(0.5 * m.activities / x.max_activities * 100
                       + 0.3 * m.participations / x.max_participations * 100
                       + 0.2 * m.students / x.max_students * 100, 2) AS activity_score
            FROM metrics m CROSS JOIN maxima x
            ORDER BY activity_score DESC, m.name, m.id
            LIMIT :limit
            """
        ),
        {"limit": limit},
    ).mappings().all()
    return [
        {**dict(row), "activity_score": float(row["activity_score"])}
        for row in rows
    ]


def benchmark_simple_ranking(
    connection: Connection,
    dimension: str,
    limit: int,
) -> list[dict[str, Any]]:
    queries = {
        "activity": """
            SELECT a.id,
                   (SELECT COUNT(*) FROM activity_registrations ar
                    WHERE ar.activity_id = a.id AND ar.status = 'registered') AS registrations,
                   (SELECT COUNT(*) FROM activity_attendance aa
                    WHERE aa.activity_id = a.id AND aa.status IN ('present', 'late')) AS attendance
            FROM activities a WHERE a.status = 'completed'
            ORDER BY attendance DESC, a.title, a.id LIMIT :limit
        """,
        "student": """
            SELECT s.id, COUNT(aa.id) AS participations,
                   COUNT(DISTINCT a.club_id) AS clubs,
                   COUNT(DISTINCT a.category_id) AS categories
            FROM students s
            JOIN activity_attendance aa ON aa.student_id = s.id AND aa.status IN ('present', 'late')
            JOIN activities a ON a.id = aa.activity_id AND a.status = 'completed'
            GROUP BY s.id, s.name ORDER BY participations DESC, s.name, s.id LIMIT :limit
        """,
        "college": """
            SELECT co.id, COUNT(aa.id) AS participations,
                   COUNT(DISTINCT aa.student_id) AS students,
                   COUNT(DISTINCT a.id) AS activities
            FROM colleges co JOIN students s ON s.college_id = co.id
            JOIN activity_attendance aa ON aa.student_id = s.id AND aa.status IN ('present', 'late')
            JOIN activities a ON a.id = aa.activity_id AND a.status = 'completed'
            GROUP BY co.id, co.name ORDER BY participations DESC, co.name, co.id LIMIT :limit
        """,
    }
    rows = connection.execute(text(queries[dimension]), {"limit": limit}).mappings().all()
    return [dict(row) for row in rows]


def benchmark_distribution(connection: Connection, dimension: str) -> list[dict[str, Any]]:

    if dimension == "college":
        rows = connection.execute(
            text(
                """
                SELECT co.id, COUNT(aa.id) AS participations,
                       COUNT(DISTINCT aa.student_id) AS students,
                       COUNT(DISTINCT a.id) AS activities
                FROM colleges co JOIN students s ON s.college_id = co.id
                JOIN activity_attendance aa ON aa.student_id = s.id AND aa.status IN ('present', 'late')
                JOIN activities a ON a.id = aa.activity_id AND a.status = 'completed'
                GROUP BY co.id, co.name ORDER BY participations DESC, co.name, co.id
                """
            )
        ).mappings().all()
        return [dict(row) for row in rows]
    if dimension == "campus":
        rows = connection.execute(text("""
            SELECT ca.id, COUNT(DISTINCT a.id) AS activities,
                   COUNT(aa.id) AS participations,
                   COUNT(DISTINCT aa.student_id) AS students
            FROM campuses ca JOIN venues v ON v.campus_id = ca.id
            JOIN activities a ON a.venue_id = v.id AND a.status = 'completed'
            LEFT JOIN activity_attendance aa
              ON aa.activity_id = a.id AND aa.status IN ('present', 'late')
            GROUP BY ca.id, ca.name
            ORDER BY participations DESC, ca.name, ca.id
        """)).mappings().all()
        return [dict(row) for row in rows]
    table, alias, join_condition = ("activity_categories", "ac", "a.category_id = ac.id")
    rows = connection.execute(
        text(
            f"""
            SELECT {alias}.id, COUNT(DISTINCT a.id) AS activities,
                   COUNT(aa.id) AS participations,
                   COUNT(DISTINCT aa.student_id) AS students
            FROM {table} {alias}
            JOIN activities a ON {join_condition} AND a.status = 'completed'
            JOIN venues v ON v.id = a.venue_id
            LEFT JOIN activity_attendance aa
              ON aa.activity_id = a.id AND aa.status IN ('present', 'late')
            GROUP BY {alias}.id, {alias}.name
            ORDER BY participations DESC, {alias}.name, {alias}.id
            """
        )
    ).mappings().all()
    return [dict(row) for row in rows]
