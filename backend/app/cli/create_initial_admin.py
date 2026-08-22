from __future__ import annotations

from sqlalchemy import text

from app.core.config import Settings, get_settings
from app.core.security import hash_password
from app.db.session import create_engine_from_url


def create_initial_admin(settings: Settings) -> bool:
    if not settings.initial_admin_password:
        raise RuntimeError("INITIAL_ADMIN_PASSWORD must be set")
    engine = create_engine_from_url(settings.database_url)
    try:
        with engine.begin() as connection:
            existing = connection.scalar(
                text("SELECT id FROM users WHERE username = :username"),
                {"username": settings.initial_admin_username},
            )
            if existing is not None:
                return False
            connection.execute(
                text(
                    """
                    INSERT INTO users
                        (username, password_hash, role, student_id, status, created_at)
                    VALUES
                        (:username, :password_hash, 'admin', NULL, 'active', UTC_TIMESTAMP())
                    """
                ),
                {
                    "username": settings.initial_admin_username,
                    "password_hash": hash_password(settings.initial_admin_password),
                },
            )
            return True
    finally:
        engine.dispose()


def main() -> None:
    created = create_initial_admin(get_settings())
    print("Initial administrator created." if created else "Administrator already exists.")


if __name__ == "__main__":
    main()
