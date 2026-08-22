from __future__ import annotations

from sqlalchemy import text

from app.core.config import Settings, get_settings
from app.core.security import hash_password
from app.db.session import create_engine_from_url


def create_demo_users(settings: Settings) -> list[str]:
    if not settings.seed_user_password:
        raise RuntimeError("SEED_USER_PASSWORD must be set")
    engine = create_engine_from_url(settings.database_url)
    created: list[str] = []
    try:
        with engine.begin() as connection:
            student_ids = connection.scalars(
                text("SELECT id FROM students WHERE status = 'active' ORDER BY id LIMIT 2")
            ).all()
            club_id = connection.scalar(
                text("SELECT id FROM clubs WHERE status = 'active' ORDER BY id LIMIT 1")
            )
            if len(student_ids) < 2 or club_id is None:
                raise RuntimeError("Seed students and clubs are required")
            accounts = (
                ("club_manager_demo", "club_manager", student_ids[0]),
                ("student_demo", "student", student_ids[1]),
            )
            for username, role, student_id in accounts:
                user_id = connection.scalar(
                    text("SELECT id FROM users WHERE username = :username"),
                    {"username": username},
                )
                if user_id is None:
                    result = connection.execute(
                        text(
                            """
                            INSERT INTO users
                                (username, password_hash, role, student_id, status, created_at)
                            VALUES
                                (:username, :password_hash, :role, :student_id,
                                 'active', UTC_TIMESTAMP())
                            """
                        ),
                        {
                            "username": username,
                            "password_hash": hash_password(settings.seed_user_password),
                            "role": role,
                            "student_id": student_id,
                        },
                    )
                    user_id = int(result.lastrowid)
                    created.append(username)
                if role == "club_manager":
                    connection.execute(
                        text(
                            """
                            INSERT INTO user_club_roles (user_id, club_id, role)
                            VALUES (:user_id, :club_id, 'manager')
                            ON DUPLICATE KEY UPDATE role = VALUES(role)
                            """
                        ),
                        {"user_id": user_id, "club_id": club_id},
                    )
        return created
    finally:
        engine.dispose()


def main() -> None:
    created = create_demo_users(get_settings())
    print("Created: " + ", ".join(created) if created else "Demo users already exist.")


if __name__ == "__main__":
    main()
