from __future__ import annotations

from typing import Any

from sqlalchemy import Connection, text


class ClubService:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def list_clubs(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        category_id: int | None = None,
        campus_id: int | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        clauses = ["1 = 1"]
        params: dict[str, Any] = {}
        if search and search.strip():
            clauses.append("(c.name LIKE :search OR c.code LIKE :search)")
            params["search"] = f"%{search.strip()}%"
        if category_id is not None:
            clauses.append("c.category_id = :category_id")
            params["category_id"] = category_id
        if campus_id is not None:
            clauses.append("c.home_campus_id = :campus_id")
            params["campus_id"] = campus_id
        if status is not None:
            clauses.append("c.status = :status")
            params["status"] = status
        where = " AND ".join(clauses)
        total = self.connection.execute(
            text(f"SELECT COUNT(*) FROM clubs c WHERE {where}"), params
        ).scalar_one()
        rows = self.connection.execute(
            text(
                f"""
                SELECT c.id, c.code, c.name, c.advisor_name, c.founded_date, c.status,
                       cc.id AS category_id, cc.name AS category_name,
                       ca.id AS campus_id, ca.name AS campus_name,
                       s.name AS leader_name,
                       (SELECT COUNT(*) FROM club_memberships cm
                        WHERE cm.club_id = c.id AND cm.status = 'active') AS member_count,
                       (SELECT COUNT(*) FROM activities a
                        WHERE a.club_id = c.id AND a.status = 'completed') AS activity_count,
                       (SELECT COUNT(*) FROM activity_attendance aa
                        JOIN activities a ON a.id = aa.activity_id
                        WHERE a.club_id = c.id AND aa.status IN ('present', 'late')) AS participation_count
                FROM clubs c
                JOIN club_categories cc ON cc.id = c.category_id
                JOIN campuses ca ON ca.id = c.home_campus_id
                LEFT JOIN students s ON s.id = c.leader_student_id
                WHERE {where}
                ORDER BY participation_count DESC, member_count DESC, c.name
                LIMIT :limit OFFSET :offset
                """
            ),
            {**params, "limit": page_size, "offset": (page - 1) * page_size},
        ).mappings().all()
        summary = self.connection.execute(
            text(
                """
                SELECT
                    (SELECT COUNT(*) FROM clubs WHERE status = 'active') AS active_clubs,
                    (SELECT COUNT(*) FROM club_categories WHERE is_active = 1) AS category_count,
                    (SELECT COUNT(*) FROM club_memberships WHERE status = 'active') AS memberships,
                    (SELECT COUNT(*) FROM activities WHERE status = 'completed') AS completed_activities
                """
            )
        ).mappings().one()
        categories = self.connection.execute(
            text("SELECT id, name FROM club_categories WHERE is_active = 1 ORDER BY id")
        ).mappings().all()
        campuses = self.connection.execute(
            text("SELECT id, name FROM campuses WHERE is_active = 1 ORDER BY id")
        ).mappings().all()
        return {
            "items": [dict(row) for row in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
            "summary": dict(summary),
            "options": {
                "categories": [dict(row) for row in categories],
                "campuses": [dict(row) for row in campuses],
            },
        }

    def get_club(self, club_id: int) -> dict[str, Any] | None:
        club = self.connection.execute(
            text(
                """
                SELECT c.id, c.code, c.name, c.advisor_name, c.founded_date,
                       c.description, c.status, cc.name AS category_name,
                       ca.name AS campus_name, s.name AS leader_name,
                       s.student_no AS leader_student_no
                FROM clubs c
                JOIN club_categories cc ON cc.id = c.category_id
                JOIN campuses ca ON ca.id = c.home_campus_id
                LEFT JOIN students s ON s.id = c.leader_student_id
                WHERE c.id = :club_id
                """
            ),
            {"club_id": club_id},
        ).mappings().one_or_none()
        if club is None:
            return None
        metrics = self.connection.execute(
            text(
                """
                SELECT
                    (SELECT COUNT(*) FROM club_memberships
                     WHERE club_id = :club_id AND status = 'active') AS member_count,
                    (SELECT COUNT(*) FROM club_memberships
                     WHERE club_id = :club_id AND status = 'active' AND role IN ('leader', 'core')) AS core_member_count,
                    (SELECT COUNT(*) FROM activities
                     WHERE club_id = :club_id AND status = 'completed') AS activity_count,
                    (SELECT COUNT(*) FROM activity_registrations ar
                     JOIN activities a ON a.id = ar.activity_id
                     WHERE a.club_id = :club_id AND ar.status = 'registered') AS registration_count,
                    (SELECT COUNT(*) FROM activity_attendance aa
                     JOIN activities a ON a.id = aa.activity_id
                     WHERE a.club_id = :club_id AND aa.status IN ('present', 'late')) AS participation_count,
                    ROUND(100 *
                        (SELECT COUNT(*) FROM activity_attendance aa
                         JOIN activities a ON a.id = aa.activity_id
                         WHERE a.club_id = :club_id AND aa.status IN ('present', 'late')) /
                        NULLIF((SELECT COUNT(*) FROM activity_registrations ar
                                JOIN activities a ON a.id = ar.activity_id
                                WHERE a.club_id = :club_id AND ar.status = 'registered'), 0), 2
                    ) AS attendance_rate
                """
            ),
            {"club_id": club_id},
        ).mappings().one()
        role_distribution = self.connection.execute(
            text(
                """
                SELECT role, COUNT(*) AS count
                FROM club_memberships
                WHERE club_id = :club_id AND status = 'active'
                GROUP BY role
                ORDER BY FIELD(role, 'leader', 'core', 'member')
                """
            ),
            {"club_id": club_id},
        ).mappings().all()
        recent_activities = self.connection.execute(
            text(
                """
                SELECT a.id, a.title, ac.name AS category_name, a.start_time,
                       a.status, a.capacity, v.name AS venue_name,
                       COUNT(DISTINCT CASE WHEN ar.status = 'registered' THEN ar.id END) AS registrations,
                       COUNT(DISTINCT CASE WHEN aa.status IN ('present', 'late') THEN aa.id END) AS attendance
                FROM activities a
                JOIN activity_categories ac ON ac.id = a.category_id
                JOIN venues v ON v.id = a.venue_id
                LEFT JOIN activity_registrations ar ON ar.activity_id = a.id
                LEFT JOIN activity_attendance aa ON aa.registration_id = ar.id
                WHERE a.club_id = :club_id
                GROUP BY a.id, a.title, ac.name, a.start_time, a.status, a.capacity, v.name
                ORDER BY a.start_time DESC
                LIMIT 8
                """
            ),
            {"club_id": club_id},
        ).mappings().all()
        active_members = self.connection.execute(
            text(
                """
                SELECT s.id, s.name, s.student_no, co.name AS college_name, cm.role,
                       COUNT(CASE WHEN aa.status IN ('present', 'late') AND a.id IS NOT NULL THEN 1 END) AS participations
                FROM club_memberships cm
                JOIN students s ON s.id = cm.student_id
                JOIN colleges co ON co.id = s.college_id
                LEFT JOIN activity_attendance aa ON aa.student_id = s.id
                LEFT JOIN activities a ON a.id = aa.activity_id AND a.club_id = cm.club_id
                WHERE cm.club_id = :club_id AND cm.status = 'active'
                GROUP BY s.id, s.name, s.student_no, co.name, cm.role
                ORDER BY FIELD(cm.role, 'leader', 'core', 'member'), participations DESC, s.student_no
                LIMIT 10
                """
            ),
            {"club_id": club_id},
        ).mappings().all()
        return {
            **dict(club),
            "metrics": dict(metrics),
            "role_distribution": [dict(row) for row in role_distribution],
            "recent_activities": [dict(row) for row in recent_activities],
            "active_members": [dict(row) for row in active_members],
        }
