from __future__ import annotations

from sqlalchemy import Engine, delete, func, select
from sqlalchemy.engine import make_url

import app.models  # noqa: F401
from app.data_generator.config import PROJECT_DATABASES
from app.data_generator.generator import DataGraph
from app.db.base import Base


def assert_project_database_url(url: str) -> str:
    try:
        parsed = make_url(url)
    except Exception as exc:
        raise RuntimeError("Seed requires a local project MySQL database") from exc
    if (
        not parsed.drivername.startswith("mysql+")
        or parsed.host not in {"127.0.0.1", "localhost"}
        or parsed.database not in PROJECT_DATABASES
    ):
        raise RuntimeError(
            "Seed and reset are restricted to the local szut_club_agent project databases"
        )
    return parsed.database


def seed_database(engine: Engine, database_url: str, graph: DataGraph, *, reset: bool) -> None:
    assert_project_database_url(database_url)
    students_table = Base.metadata.tables["students"]
    with engine.begin() as connection:
        existing = connection.scalar(select(func.count()).select_from(students_table)) or 0
        if existing and not reset:
            raise RuntimeError("Project database already contains data; use --reset explicitly")
        if reset:
            for table in reversed(Base.metadata.sorted_tables):
                connection.execute(delete(table))
        for table in Base.metadata.sorted_tables:
            rows = graph.tables.get(table.name)
            if rows:
                connection.execute(table.insert(), rows)
