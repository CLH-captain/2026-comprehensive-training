from __future__ import annotations

from typing import Any

from sqlalchemy import Connection, text


class StudentService:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    @staticmethod
    def _where(
        *,
        search: str | None,
        college_id: int | None,
        major_id: int | None,
        grade_no: int | None,
        status: str | None,
    ) -> tuple[str, dict[str, Any]]:
        clauses = ["1 = 1"]
        params: dict[str, Any] = {}
        if search and search.strip():
            clauses.append("(s.student_no LIKE :search OR s.name LIKE :search)")
            params["search"] = f"%{search.strip()}%"
        if college_id is not None:
            clauses.append("s.college_id = :college_id")
            params["college_id"] = college_id
        if major_id is not None:
            clauses.append("s.major_id = :major_id")
            params["major_id"] = major_id
        if grade_no is not None:
            clauses.append("s.grade_no = :grade_no")
            params["grade_no"] = grade_no
        if status is not None:
            clauses.append("s.status = :status")
            params["status"] = status
        return " AND ".join(clauses), params

    def list_students(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        college_id: int | None = None,
        major_id: int | None = None,
        grade_no: int | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        where, params = self._where(
            search=search,
            college_id=college_id,
            major_id=major_id,
            grade_no=grade_no,
            status=status,
        )
        total = self.connection.execute(
            text(f"SELECT COUNT(*) FROM students s WHERE {where}"),
            params,
        ).scalar_one()
        query_params = {**params, "limit": page_size, "offset": (page - 1) * page_size}
        rows = self.connection.execute(
            text(
                f"""
                SELECT s.id, s.student_no, s.name, s.gender, s.grade_no, s.class_name,
                       s.status, co.id AS college_id, co.name AS college_name,
                       m.id AS major_id, m.name AS major_name,
                       (SELECT COUNT(*) FROM club_memberships cm
                        WHERE cm.student_id = s.id AND cm.status = 'active') AS club_count,
                       (SELECT COUNT(*) FROM activity_attendance aa
                        WHERE aa.student_id = s.id AND aa.status IN ('present', 'late')) AS participation_count,
                       (SELECT MAX(a.start_time) FROM activity_attendance aa
                        JOIN activities a ON a.id = aa.activity_id
                        WHERE aa.student_id = s.id AND aa.status IN ('present', 'late')) AS last_activity_at
                FROM students s
                JOIN colleges co ON co.id = s.college_id
                JOIN majors m ON m.id = s.major_id
                WHERE {where}
                ORDER BY participation_count DESC, s.student_no
                LIMIT :limit OFFSET :offset
                """
            ),
            query_params,
        ).mappings().all()
        summary = self.connection.execute(
            text(
                """
                SELECT
                    (SELECT COUNT(*) FROM students WHERE status = 'active') AS total_students,
                    (SELECT COUNT(*) FROM colleges WHERE is_active = 1) AS college_count,
                    (SELECT COUNT(DISTINCT student_id) FROM activity_attendance
                     WHERE status IN ('present', 'late')) AS participating_students,
                    (SELECT COUNT(DISTINCT student_id) FROM club_memberships
                     WHERE status = 'active') AS club_members
                """
            )
        ).mappings().one()
        colleges = self.connection.execute(
            text("SELECT id, name FROM colleges WHERE is_active = 1 ORDER BY name")
        ).mappings().all()
        majors = self.connection.execute(
            text("SELECT id, college_id, name FROM majors WHERE is_active = 1 ORDER BY name")
        ).mappings().all()
        return {
            "items": [dict(row) for row in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
            "summary": dict(summary),
            "options": {
                "colleges": [dict(row) for row in colleges],
                "majors": [dict(row) for row in majors],
            },
        }

    def get_student(self, student_id: int) -> dict[str, Any] | None:
        student = self.connection.execute(
            text(
                """
                SELECT s.id, s.student_no, s.name, s.gender, s.enrollment_year,
                       s.grade_no, s.class_name, s.status, s.created_at,
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
        summary = self.connection.execute(
            text(
                """
                SELECT
                    (SELECT COUNT(*) FROM club_memberships
                     WHERE student_id = :student_id AND status = 'active') AS club_count,
                    (SELECT COUNT(*) FROM activity_registrations
                     WHERE student_id = :student_id AND status = 'registered') AS registration_count,
                    (SELECT COUNT(*) FROM activity_attendance
                     WHERE student_id = :student_id AND status IN ('present', 'late')) AS participation_count,
                    ROUND(100 *
                        (SELECT COUNT(*) FROM activity_attendance
                         WHERE student_id = :student_id AND status IN ('present', 'late')) /
                        NULLIF((SELECT COUNT(*) FROM activity_registrations
                                WHERE student_id = :student_id AND status = 'registered'), 0), 2
                    ) AS attendance_rate
                """
            ),
            {"student_id": student_id},
        ).mappings().one()
        clubs = self.connection.execute(
            text(
                """
                SELECT c.id, c.name, cc.name AS category_name, cm.role, cm.join_date
                FROM club_memberships cm
                JOIN clubs c ON c.id = cm.club_id
                JOIN club_categories cc ON cc.id = c.category_id
                WHERE cm.student_id = :student_id AND cm.status = 'active'
                ORDER BY FIELD(cm.role, 'leader', 'core', 'member'), c.name
                """
            ),
            {"student_id": student_id},
        ).mappings().all()
        recent_activities = self.connection.execute(
            text(
                """
                SELECT a.id, a.title, c.name AS club_name, ac.name AS category_name,
                       a.start_time, aa.status AS attendance_status
                FROM activity_attendance aa
                JOIN activities a ON a.id = aa.activity_id
                JOIN clubs c ON c.id = a.club_id
                JOIN activity_categories ac ON ac.id = a.category_id
                WHERE aa.student_id = :student_id
                ORDER BY a.start_time DESC, a.id DESC
                LIMIT 8
                """
            ),
            {"student_id": student_id},
        ).mappings().all()
        return {
            **dict(student),
            "participation_summary": dict(summary),
            "clubs": [dict(row) for row in clubs],
            "recent_activities": [dict(row) for row in recent_activities],
        }
