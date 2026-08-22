from collections.abc import Iterator

import pytest
from sqlalchemy import Connection, create_engine, text

from app.core.config import get_settings
from app.db.session import assert_test_database_url


@pytest.fixture(scope="session")
def statistics_connection() -> Iterator[Connection]:
    url = get_settings().test_database_url
    assert_test_database_url(url)
    engine = create_engine(url)
    with engine.connect() as connection:
        student_count = connection.scalar(text("SELECT COUNT(*) FROM students"))
        if student_count != 3000:
            pytest.fail("statistics tests require the fixed seed in szut_club_agent_test")
        yield connection
    engine.dispose()
