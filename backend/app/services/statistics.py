from __future__ import annotations

from typing import Any

from sqlalchemy import Connection, text


class StatisticsService:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    @staticmethod
    def _filters(term_id: int | None, campus_id: int | None, prefix: str = "a") -> tuple[str, dict[str, int]]:
        clauses: list[str] = []
        params: dict[str, int] = {}
        if term_id is not None:
            clauses.append(f"{prefix}.term_id = :term_id")
            params["term_id"] = term_id
        if campus_id is not None:
            clauses.append("v.campus_id = :campus_id")
            params["campus_id"] = campus_id
        return (" AND " + " AND ".join(clauses) if clauses else "", params)

    def dashboard(self, term_id: int | None = None, campus_id: int | None = None) -> dict[str, Any]:
        activity_filter, params = self._filters(term_id, campus_id)
        overview = self.connection.execute(
            text(
                f"""
                SELECT
                    (SELECT COUNT(*) FROM clubs WHERE status = 'active') AS active_clubs,
                    COUNT(DISTINCT CASE WHEN a.status = 'completed' THEN a.id END) AS completed_activities,
                    COUNT(CASE WHEN aa.status IN ('present', 'late') AND a.status = 'completed' THEN 1 END) AS participations,
                    COUNT(DISTINCT CASE WHEN aa.status IN ('present', 'late') AND a.status = 'completed' THEN aa.student_id END) AS active_students,
                    ROUND(
                        100 * COUNT(CASE WHEN aa.status IN ('present', 'late') AND a.status = 'completed' THEN 1 END)
                        / NULLIF(COUNT(CASE WHEN ar.status = 'registered' AND a.status = 'completed' THEN 1 END), 0), 2
                    ) AS attendance_rate
                FROM activities a
                JOIN venues v ON v.id = a.venue_id
                LEFT JOIN activity_registrations ar ON ar.activity_id = a.id
                LEFT JOIN activity_attendance aa ON aa.registration_id = ar.id
                WHERE 1 = 1 {activity_filter}
                """
            ),
            params,
        ).mappings().one()

        monthly = self.connection.execute(
            text(
                f"""
                SELECT DATE_FORMAT(a.start_time, '%Y-%m') AS month,
                       COUNT(DISTINCT CASE WHEN a.status = 'completed' THEN a.id END) AS activities,
                       COUNT(CASE WHEN aa.status IN ('present', 'late') THEN 1 END) AS participations
                FROM activities a
                JOIN venues v ON v.id = a.venue_id
                LEFT JOIN activity_attendance aa ON aa.activity_id = a.id
                WHERE a.status = 'completed' {activity_filter}
                GROUP BY DATE_FORMAT(a.start_time, '%Y-%m')
                ORDER BY month
                """
            ),
            params,
        ).mappings().all()

        club_ranking = self.connection.execute(
            text(
                f"""
                SELECT c.id, c.name,
                       COUNT(DISTINCT CASE WHEN a.status = 'completed' THEN a.id END) AS activities,
                       COUNT(CASE WHEN aa.status IN ('present', 'late') THEN 1 END) AS participations
                FROM clubs c
                LEFT JOIN activities a ON a.club_id = c.id
                LEFT JOIN venues v ON v.id = a.venue_id
                LEFT JOIN activity_attendance aa ON aa.activity_id = a.id
                WHERE c.status = 'active' {activity_filter}
                GROUP BY c.id, c.name
                ORDER BY participations DESC, activities DESC, c.name, c.id
                LIMIT 8
                """
            ),
            params,
        ).mappings().all()

        college_ranking = self.connection.execute(
            text(
                f"""
                SELECT co.id, co.name,
                       COUNT(CASE WHEN aa.status IN ('present', 'late') THEN 1 END) AS participations,
                       COUNT(DISTINCT CASE WHEN aa.status IN ('present', 'late') THEN aa.student_id END) AS students
                FROM colleges co
                JOIN students s ON s.college_id = co.id
                JOIN activity_attendance aa ON aa.student_id = s.id
                JOIN activities a ON a.id = aa.activity_id AND a.status = 'completed'
                JOIN venues v ON v.id = a.venue_id
                WHERE aa.status IN ('present', 'late') {activity_filter}
                GROUP BY co.id, co.name
                ORDER BY participations DESC, co.name, co.id
                LIMIT 8
                """
            ),
            params,
        ).mappings().all()

        category_distribution = self.connection.execute(
            text(
                f"""
                SELECT ac.id, ac.name,
                       COUNT(DISTINCT a.id) AS activities,
                       COUNT(CASE WHEN aa.status IN ('present', 'late') THEN 1 END) AS participations
                FROM activity_categories ac
                JOIN activities a ON a.category_id = ac.id AND a.status = 'completed'
                JOIN venues v ON v.id = a.venue_id
                LEFT JOIN activity_attendance aa ON aa.activity_id = a.id
                WHERE 1 = 1 {activity_filter}
                GROUP BY ac.id, ac.name
                ORDER BY participations DESC, ac.name
                """
            ),
            params,
        ).mappings().all()

        top_activities = self.connection.execute(
            text(
                f"""
                SELECT a.id, a.title, c.name AS club_name, a.start_time,
                       COUNT(CASE WHEN ar.status = 'registered' THEN 1 END) AS registrations,
                       COUNT(CASE WHEN aa.status IN ('present', 'late') THEN 1 END) AS attendance,
                       ROUND(100 * COUNT(CASE WHEN aa.status IN ('present', 'late') THEN 1 END)
                           / NULLIF(COUNT(CASE WHEN ar.status = 'registered' THEN 1 END), 0), 2) AS attendance_rate
                FROM activities a
                JOIN clubs c ON c.id = a.club_id
                JOIN venues v ON v.id = a.venue_id
                LEFT JOIN activity_registrations ar ON ar.activity_id = a.id
                LEFT JOIN activity_attendance aa ON aa.registration_id = ar.id
                WHERE a.status = 'completed' {activity_filter}
                GROUP BY a.id, a.title, c.name, a.start_time
                ORDER BY attendance DESC, a.title, a.id
                LIMIT 6
                """
            ),
            params,
        ).mappings().all()

        contexts = {
            "terms": [dict(row) for row in self.connection.execute(text("SELECT id, name, is_default FROM academic_terms ORDER BY start_date")).mappings()],
            "campuses": [dict(row) for row in self.connection.execute(text("SELECT id, name FROM campuses WHERE is_active = 1 ORDER BY id")).mappings()],
        }
        return {
            "overview": dict(overview),
            "monthly_trend": [dict(row) for row in monthly],
            "club_ranking": [dict(row) for row in club_ranking],
            "college_ranking": [dict(row) for row in college_ranking],
            "category_distribution": [dict(row) for row in category_distribution],
            "top_activities": [dict(row) for row in top_activities],
            "contexts": contexts,
        }
