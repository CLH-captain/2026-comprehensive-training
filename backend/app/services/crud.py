from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, ClassVar

from sqlalchemy import Connection, text

from app.core.errors import AppError


class CrudService:
    DICTIONARIES: ClassVar[dict[str, tuple[str, ...]]] = {
        "campuses": ("code", "name", "address"),
        "terms": ("academic_year", "term_no", "name", "start_date", "end_date"),
        "colleges": ("code", "name", "primary_campus_id"),
        "majors": ("college_id", "code", "name", "duration_years"),
        "club-categories": ("name", "description"),
        "activity-categories": ("name", "description"),
        "venues": ("campus_id", "code", "name", "venue_type", "capacity"),
    }
    TABLES: ClassVar[dict[str, str]] = {
        "terms": "academic_terms",
        "club-categories": "club_categories",
        "activity-categories": "activity_categories",
    }

    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def _insert(self, table: str, data: dict[str, Any]) -> int:
        columns = ", ".join(data)
        placeholders = ", ".join(f":{key}" for key in data)
        result = self.connection.execute(
            text(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"), data
        )
        return int(result.lastrowid)

    def _update(self, table: str, record_id: int, data: dict[str, Any]) -> None:
        if not data:
            return
        assignments = ", ".join(f"{key} = :{key}" for key in data)
        result = self.connection.execute(
            text(f"UPDATE {table} SET {assignments} WHERE id = :record_id"),
            {**data, "record_id": record_id},
        )
        if result.rowcount == 0:
            raise AppError(404, "NOT_FOUND", "Record not found")

    def _one(self, table: str, record_id: int) -> dict[str, Any]:
        row = self.connection.execute(
            text(f"SELECT * FROM {table} WHERE id = :record_id"),
            {"record_id": record_id},
        ).mappings().one_or_none()
        if row is None:
            raise AppError(404, "NOT_FOUND", "Record not found")
        return dict(row)

    def list_dictionary(self, resource: str) -> list[dict[str, Any]]:
        table = self.TABLES.get(resource, resource)
        columns = self.DICTIONARIES[resource]
        selected = ", ".join(("id", *columns))
        rows = self.connection.execute(
            text(f"SELECT {selected} FROM {table} ORDER BY name, id")
        ).mappings().all()
        return [dict(row) for row in rows]

    def create_dictionary(self, resource: str, data: dict[str, Any]) -> dict[str, Any]:
        table = self.TABLES.get(resource, resource)
        allowed = self.DICTIONARIES[resource]
        values = {key: value for key, value in data.items() if key in allowed}
        record_id = self._insert(table, values)
        return self._one(table, record_id)

    def update_dictionary(
        self, resource: str, record_id: int, data: dict[str, Any]
    ) -> dict[str, Any]:
        table = self.TABLES.get(resource, resource)
        allowed = self.DICTIONARIES[resource]
        values = {key: value for key, value in data.items() if key in allowed}
        self._update(table, record_id, values)
        return self._one(table, record_id)

    def deactivate_dictionary(self, resource: str, record_id: int) -> None:
        table = self.TABLES.get(resource, resource)
        active_tables = {
            "campuses",
            "colleges",
            "majors",
            "club_categories",
            "activity_categories",
            "venues",
        }
        if table not in active_tables:
            raise AppError(409, "DELETE_NOT_SUPPORTED", "This resource cannot be disabled")
        self._update(table, record_id, {"is_active": False})

    def create_student(self, data: dict[str, Any]) -> dict[str, Any]:
        record_id = self._insert("students", {**data, "created_at": datetime.now(UTC).replace(tzinfo=None)})
        return self._one("students", record_id)

    def update_student(self, student_id: int, data: dict[str, Any]) -> dict[str, Any]:
        self._update("students", student_id, data)
        return self._one("students", student_id)

    def deactivate_student(self, student_id: int) -> None:
        self._update("students", student_id, {"status": "suspended"})

    def create_club(self, data: dict[str, Any]) -> dict[str, Any]:
        record_id = self._insert("clubs", data)
        return self._one("clubs", record_id)

    def update_club(self, club_id: int, data: dict[str, Any]) -> dict[str, Any]:
        self._update("clubs", club_id, data)
        return self._one("clubs", club_id)

    def deactivate_club(self, club_id: int) -> None:
        self._update("clubs", club_id, {"status": "inactive"})

    def upsert_membership(self, club_id: int, data: dict[str, Any]) -> dict[str, Any]:
        self.connection.execute(
            text(
                """
                INSERT INTO club_memberships
                    (club_id, student_id, role, join_date, status)
                VALUES
                    (:club_id, :student_id, :role, :join_date, :status)
                ON DUPLICATE KEY UPDATE role = VALUES(role),
                    join_date = VALUES(join_date), status = VALUES(status)
                """
            ),
            {"club_id": club_id, **data},
        )
        row = self.connection.execute(
            text(
                """
                SELECT * FROM club_memberships
                WHERE club_id = :club_id AND student_id = :student_id
                """
            ),
            {"club_id": club_id, "student_id": data["student_id"]},
        ).mappings().one()
        return dict(row)

    def list_memberships(self, club_id: int) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            text(
                """
                SELECT cm.*, s.student_no, s.name AS student_name
                FROM club_memberships cm JOIN students s ON s.id = cm.student_id
                WHERE cm.club_id = :club_id
                ORDER BY FIELD(cm.role, 'leader', 'core', 'member'), s.student_no
                """
            ),
            {"club_id": club_id},
        ).mappings().all()
        return [dict(row) for row in rows]

    def create_activity(self, data: dict[str, Any]) -> dict[str, Any]:
        record_id = self._insert("activities", {**data, "created_at": datetime.now(UTC).replace(tzinfo=None)})
        return self._one("activities", record_id)

    def update_activity(self, activity_id: int, data: dict[str, Any]) -> dict[str, Any]:
        current = self._one("activities", activity_id)
        start = data.get("start_time", current["start_time"])
        end = data.get("end_time", current["end_time"])
        if start >= end:
            raise AppError(422, "INVALID_TIME_RANGE", "Activity start must precede end")
        self._update("activities", activity_id, data)
        return self._one("activities", activity_id)

    def activity_club_id(self, activity_id: int) -> int:
        club_id = self.connection.scalar(
            text("SELECT club_id FROM activities WHERE id = :activity_id"),
            {"activity_id": activity_id},
        )
        if club_id is None:
            raise AppError(404, "NOT_FOUND", "Activity not found")
        return int(club_id)

    def delete_activity(self, activity_id: int) -> str:
        self._one("activities", activity_id)
        references = self.connection.scalar(
            text(
                """
                SELECT (SELECT COUNT(*) FROM activity_registrations WHERE activity_id = :id)
                     + (SELECT COUNT(*) FROM activity_attendance WHERE activity_id = :id)
                """
            ),
            {"id": activity_id},
        )
        if references:
            self._update("activities", activity_id, {"status": "cancelled"})
            return "cancelled"
        self.connection.execute(
            text("DELETE FROM activities WHERE id = :id"), {"id": activity_id}
        )
        return "deleted"

    def create_registration(self, data: dict[str, Any]) -> dict[str, Any]:
        activity = self._one("activities", data["activity_id"])
        if activity["status"] not in ("published", "completed"):
            raise AppError(409, "ACTIVITY_NOT_OPEN", "Activity is not open for registration")
        registered = self.connection.scalar(
            text(
                """
                SELECT COUNT(*) FROM activity_registrations
                WHERE activity_id = :activity_id AND status = 'registered'
                """
            ),
            {"activity_id": data["activity_id"]},
        )
        status = "registered" if registered < activity["capacity"] else "waitlisted"
        record_id = self._insert(
            "activity_registrations",
            {
                **data,
                "register_time": datetime.now(UTC).replace(tzinfo=None),
                "status": status,
                "source": "web",
            },
        )
        return self._one("activity_registrations", record_id)

    def update_registration(self, registration_id: int, status: str) -> dict[str, Any]:
        self._update("activity_registrations", registration_id, {"status": status})
        return self._one("activity_registrations", registration_id)

    def registration_owner(self, registration_id: int) -> tuple[int, int]:
        row = self.connection.execute(
            text(
                """
                SELECT ar.student_id, a.club_id
                FROM activity_registrations ar
                JOIN activities a ON a.id = ar.activity_id
                WHERE ar.id = :registration_id
                """
            ),
            {"registration_id": registration_id},
        ).one_or_none()
        if row is None:
            raise AppError(404, "NOT_FOUND", "Registration not found")
        return int(row[0]), int(row[1])

    def upsert_attendance(self, data: dict[str, Any]) -> dict[str, Any]:
        registration_id = self.connection.scalar(
            text(
                """
                SELECT id FROM activity_registrations
                WHERE activity_id = :activity_id AND student_id = :student_id
                """
            ),
            data,
        )
        if registration_id is None:
            raise AppError(409, "REGISTRATION_REQUIRED", "Student is not registered")
        values = {
            **data,
            "registration_id": registration_id,
            "checkin_time": data.get("checkin_time")
            or (datetime.now(UTC).replace(tzinfo=None) if data["status"] in ("present", "late") else None),
        }
        self.connection.execute(
            text(
                """
                INSERT INTO activity_attendance
                    (activity_id, student_id, registration_id, status, checkin_time)
                VALUES
                    (:activity_id, :student_id, :registration_id, :status, :checkin_time)
                ON DUPLICATE KEY UPDATE registration_id = VALUES(registration_id),
                    status = VALUES(status), checkin_time = VALUES(checkin_time)
                """
            ),
            values,
        )
        row = self.connection.execute(
            text(
                """
                SELECT * FROM activity_attendance
                WHERE activity_id = :activity_id AND student_id = :student_id
                """
            ),
            data,
        ).mappings().one()
        return dict(row)

    def list_participation_records(
        self,
        table: str,
        *,
        activity_id: int | None,
        student_id: int | None,
        club_ids: frozenset[int] | None = None,
    ) -> list[dict[str, Any]]:
        allowed = {"activity_registrations", "activity_attendance"}
        if table not in allowed:
            raise ValueError("Unsupported participation table")
        clauses = ["1 = 1"]
        params: dict[str, Any] = {}
        if activity_id is not None:
            clauses.append("r.activity_id = :activity_id")
            params["activity_id"] = activity_id
        if student_id is not None:
            clauses.append("r.student_id = :student_id")
            params["student_id"] = student_id
        if club_ids is not None:
            if not club_ids:
                clauses.append("1 = 0")
            else:
                names = []
                for index, club_id in enumerate(sorted(club_ids)):
                    name = f"scope_club_{index}"
                    names.append(f":{name}")
                    params[name] = club_id
                clauses.append(f"a.club_id IN ({', '.join(names)})")
        rows = self.connection.execute(
            text(
                f"""
                SELECT r.*, s.student_no, s.name AS student_name, a.title AS activity_title,
                       a.club_id
                FROM {table} r JOIN students s ON s.id = r.student_id
                JOIN activities a ON a.id = r.activity_id
                WHERE {' AND '.join(clauses)} ORDER BY r.id DESC LIMIT 500
                """
            ),
            params,
        ).mappings().all()
        return [dict(row) for row in rows]