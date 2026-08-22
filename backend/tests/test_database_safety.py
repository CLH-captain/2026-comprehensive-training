import pytest

from app.db.session import assert_test_database_url


def test_accepts_the_dedicated_test_database() -> None:
    url = "mysql+pymysql://user:pass@127.0.0.1:3306/szut_club_agent_test"

    assert_test_database_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "mysql+pymysql://user:pass@127.0.0.1:3306/szut_club_agent",
        "mysql+pymysql://user:pass@127.0.0.1:3306/another_test",
        "mysql+pymysql://user:pass@127.0.0.1:3306/",
        "sqlite:///szut_club_agent_test.db",
        "",
    ],
)
def test_rejects_non_project_test_databases(url: str) -> None:
    with pytest.raises(RuntimeError, match="szut_club_agent_test"):
        assert_test_database_url(url)
