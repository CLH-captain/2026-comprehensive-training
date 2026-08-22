from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

PROJECT_TEST_DATABASE = "szut_club_agent_test"


def assert_test_database_url(url: str) -> None:
    try:
        parsed = make_url(url)
    except Exception as exc:
        raise RuntimeError(
            f"Destructive tests require the {PROJECT_TEST_DATABASE} MySQL database"
        ) from exc

    if not parsed.drivername.startswith("mysql+") or parsed.database != PROJECT_TEST_DATABASE:
        raise RuntimeError(
            f"Destructive tests require the {PROJECT_TEST_DATABASE} MySQL database"
        )


def create_engine_from_url(url: str) -> Engine:
    return create_engine(
        url,
        pool_pre_ping=True,
        pool_recycle=1800,
    )


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )
