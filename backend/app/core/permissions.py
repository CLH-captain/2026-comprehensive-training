from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlalchemy import Connection, text

from app.core.errors import AppError

if TYPE_CHECKING:
    from app.api.dependencies import CurrentUser


@dataclass(frozen=True)
class AccessScope:
    user_id: int
    role: str
    student_id: int | None
    club_ids: frozenset[int] | None

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    def permits_club(self, club_id: int) -> bool:
        return self.club_ids is None or club_id in self.club_ids

    def permits_student(self, student_id: int) -> bool:
        return self.is_admin or self.student_id == student_id

    def require_club(self, club_id: int) -> None:
        if not self.permits_club(club_id):
            raise AppError(403, "FORBIDDEN", "Club is outside your access scope")

    def require_student(self, student_id: int) -> None:
        if not self.permits_student(student_id):
            raise AppError(403, "FORBIDDEN", "Student is outside your access scope")


def load_access_scope(connection: Connection, user: CurrentUser) -> AccessScope:
    if user.role == "admin":
        club_ids: frozenset[int] | None = None
    elif user.role == "club_manager":
        club_ids = frozenset(
            connection.scalars(
                text(
                    """
                    SELECT club_id FROM user_club_roles
                    WHERE user_id = :user_id AND role = 'manager'
                    """
                ),
                {"user_id": user.id},
            ).all()
        )
    else:
        club_ids = frozenset()
    return AccessScope(user.id, user.role, user.student_id, club_ids)


def require_role(scope: AccessScope, *allowed: str) -> None:
    if scope.role not in allowed:
        raise AppError(403, "FORBIDDEN", "You do not have permission for this action")
