import pytest

from app.data_generator.seed import assert_project_database_url


@pytest.mark.parametrize(
    "url",
    [
        "mysql+pymysql://user:pass@127.0.0.1/szut_club_agent",
        "mysql+pymysql://user:pass@localhost/szut_club_agent_test",
    ],
)
def test_seed_accepts_only_project_databases(url: str) -> None:
    assert assert_project_database_url(url) in {"szut_club_agent", "szut_club_agent_test"}


@pytest.mark.parametrize(
    "url",
    [
        "mysql+pymysql://user:pass@127.0.0.1/mysql",
        "mysql+pymysql://user:pass@127.0.0.1/another_database",
        "mysql+pymysql://user:pass@192.168.1.20/szut_club_agent",
        "sqlite:///szut_club_agent.db",
    ],
)
def test_seed_rejects_non_project_databases(url: str) -> None:
    with pytest.raises(RuntimeError, match="restricted"):
        assert_project_database_url(url)
