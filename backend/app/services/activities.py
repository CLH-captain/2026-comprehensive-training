from __future__ import annotations

from typing import Any

from sqlalchemy import Connection, text


class ActivityService:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def list_activities(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        term_id: int | None = None,
        category_id: int | None = None,
        club_id: int | None = None,
        campus_id: int | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        clauses = ["1 = 1"]
        params: dict[str, Any] = {}
        filters = {
            "term_id": (term_id, "a.term_id = :term_id"),
            "category_id": (category_id, "a.category_id = :category_id"),
            "club_id": (club_id, "a.club_id = :club_id"),
            "campus_id": (campus_id, "v.campus_id = :campus_id"),
            "status": (status, "a.status = :status"),
        }
        if search and search.strip():
            clauses.append("(a.title LIKE :search OR a.code LIKE :search OR c.name LIKE :search)")
            params["search"] = f"%{search.strip()}%"
        for name, (value, clause) in filters.items():
            if value is not None:
                clauses.append(clause)
                params[name] = value
        where = " AND ".join(clauses)
        from_clause = "FROM activities a JOIN clubs c ON c.id = a.club_id JOIN venues v ON v.id = a.venue_id"
        total = self.connection.execute(
            text(f"SELECT COUNT(*) {from_clause} WHERE {where}"), params
        ).scalar_one()
        rows = self.connection.execute(
            text(
                f"""
                SELECT a.id, a.code, a.title, a.start_time, a.end_time, a.capacity, a.status,
                       c.id AS club_id, c.name AS club_name,
                       ac.id AS category_id, ac.name AS category_name,
                       t.id AS term_id, t.name AS term_name,
                       v.id AS venue_id, v.name AS venue_name,
                       ca.id AS campus_id, ca.name AS campus_name,
                       (SELECT COUNT(*) FROM activity_registrations ar
                        WHERE ar.activity_id = a.id AND ar.status = 'registered') AS registrations,
                       (SELECT COUNT(*) FROM activity_attendance aa
                        WHERE aa.activity_id = a.id AND aa.status IN ('present', 'late')) AS attendance,
                       ROUND(100 *
                           (SELECT COUNT(*) FROM activity_attendance aa
                            WHERE aa.activity_id = a.id AND aa.status IN ('present', 'late')) /
                           NULLIF((SELECT COUNT(*) FROM activity_registrations ar
                                   WHERE ar.activity_id = a.id AND ar.status = 'registered'), 0), 2
                       ) AS attendance_rate
                FROM activities a
                JOIN clubs c ON c.id = a.club_id
                JOIN activity_categories ac ON ac.id = a.category_id
                JOIN academic_terms t ON t.id = a.term_id
                JOIN venues v ON v.id = a.venue_id
                JOIN campuses ca ON ca.id = v.campus_id
                WHERE {where}
                ORDER BY a.start_time DESC, a.id DESC
                LIMIT :limit OFFSET :offset
                """
            ),
            {**params, "limit": page_size, "offset": (page - 1) * page_size},
        ).mappings().all()
        summary = self.connection.execute(
            text(
                """
                SELECT
                    (SELECT COUNT(*) FROM activities) AS total_activities,
                    (SELECT COUNT(*) FROM activities WHERE status = 'completed') AS completed_activities,
                    (SELECT COUNT(*) FROM activity_registrations WHERE status = 'registered') AS registrations,
                    (SELECT COUNT(*) FROM activity_attendance WHERE status IN ('present', 'late')) AS attendance
                """
            )
        ).mappings().one()
        options = {
            "terms": self.connection.execute(text("SELECT id, name FROM academic_terms ORDER BY start_date")).mappings().all(),
            "categories": self.connection.execute(text("SELECT id, name FROM activity_categories WHERE is_active = 1 ORDER BY id")).mappings().all(),
            "clubs": self.connection.execute(text("SELECT id, name FROM clubs WHERE status = 'active' ORDER BY name")).mappings().all(),
            "campuses": self.connection.execute(text("SELECT id, name FROM campuses WHERE is_active = 1 ORDER BY id")).mappings().all(),
            "venues": self.connection.execute(text("SELECT id, name, campus_id FROM venues WHERE is_active = 1 ORDER BY campus_id, name")).mappings().all(),
        }
        return {
            "items": [dict(row) for row in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
            "summary": dict(summary),
            "options": {key: [dict(row) for row in values] for key, values in options.items()},
        }

    def get_activity(self, activity_id: int) -> dict[str, Any] | None:
        activity = self.connection.execute(
            text(
                """
                SELECT a.id, a.code, a.title, a.description, a.start_time, a.end_time,
                       a.capacity, a.status, a.created_at, c.name AS club_name,
                       ac.name AS category_name, t.name AS term_name,
                       v.name AS venue_name, v.venue_type, ca.name AS campus_name
                FROM activities a
                JOIN clubs c ON c.id = a.club_id
                JOIN activity_categories ac ON ac.id = a.category_id
                JOIN academic_terms t ON t.id = a.term_id
                JOIN venues v ON v.id = a.venue_id
                JOIN campuses ca ON ca.id = v.campus_id
                WHERE a.id = :activity_id
                """
            ),
            {"activity_id": activity_id},
        ).mappings().one_or_none()
        if activity is None:
            return None
        metrics = self.connection.execute(
            text(
                """
                SELECT
                    (SELECT COUNT(*) FROM activity_registrations
                     WHERE activity_id = :activity_id AND status = 'registered') AS registrations,
                    (SELECT COUNT(*) FROM activity_attendance
                     WHERE activity_id = :activity_id AND status IN ('present', 'late')) AS attendance,
                    (SELECT COUNT(*) FROM activity_attendance
                     WHERE activity_id = :activity_id AND status = 'absent') AS absent,
                    ROUND(100 *
                        (SELECT COUNT(*) FROM activity_attendance
                         WHERE activity_id = :activity_id AND status IN ('present', 'late')) /
                        NULLIF((SELECT COUNT(*) FROM activity_registrations
                                WHERE activity_id = :activity_id AND status = 'registered'), 0), 2
                    ) AS attendance_rate
                """
            ),
            {"activity_id": activity_id},
        ).mappings().one()
        registrations = self.connection.execute(
            text(
                """
                SELECT status, COUNT(*) AS count
                FROM activity_registrations
                WHERE activity_id = :activity_id
                GROUP BY status
                ORDER BY FIELD(status, 'registered', 'cancelled', 'waitlisted')
                """
            ),
            {"activity_id": activity_id},
        ).mappings().all()
        attendance = self.connection.execute(
            text(
                """
                SELECT status, COUNT(*) AS count
                FROM activity_attendance
                WHERE activity_id = :activity_id
                GROUP BY status
                ORDER BY FIELD(status, 'present', 'late', 'absent')
                """
            ),
            {"activity_id": activity_id},
        ).mappings().all()
        participants = self.connection.execute(
            text(
                """
                SELECT s.id, s.name, s.student_no, co.name AS college_name,
                       ar.status AS registration_status, aa.status AS attendance_status,
                       aa.checkin_time
                FROM activity_registrations ar
                JOIN students s ON s.id = ar.student_id
                JOIN colleges co ON co.id = s.college_id
                LEFT JOIN activity_attendance aa ON aa.registration_id = ar.id
                WHERE ar.activity_id = :activity_id
                ORDER BY FIELD(aa.status, 'present', 'late', 'absent'), ar.register_time, s.student_no
                LIMIT 12
                """
            ),
            {"activity_id": activity_id},
        ).mappings().all()
        return {
            **dict(activity),
            "metrics": dict(metrics),
            "registration_distribution": [dict(row) for row in registrations],
            "attendance_distribution": [dict(row) for row in attendance],
            "participants": [dict(row) for row in participants],
        }
