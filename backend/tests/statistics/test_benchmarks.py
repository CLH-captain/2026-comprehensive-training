from sqlalchemy import Connection

from app.statistics.service import StatisticsService
from tests.statistics.benchmark_queries import (
    benchmark_club_ranking,
    benchmark_distribution,
    benchmark_monthly,
    benchmark_overview,
    benchmark_simple_ranking,
)


def _select(rows: list[dict], fields: tuple[str, ...]) -> list[dict]:
    return [{field: row[field] for field in fields} for row in rows]


def test_overview_matches_independent_sql(statistics_connection: Connection) -> None:
    service = StatisticsService(statistics_connection)
    assert service.overview() == benchmark_overview(statistics_connection)


def test_monthly_trend_matches_independent_sql(statistics_connection: Connection) -> None:
    service = StatisticsService(statistics_connection)
    assert service.monthly_trend() == benchmark_monthly(statistics_connection)


def test_all_rankings_match_independent_sql(statistics_connection: Connection) -> None:
    service = StatisticsService(statistics_connection)
    club_fields = ("id", "activities", "participations", "students", "activity_score")
    assert _select(service.ranking("club", limit=10), club_fields) == benchmark_club_ranking(
        statistics_connection, 10
    )
    for dimension, fields in (
        ("activity", ("id", "registrations", "attendance")),
        ("student", ("id", "participations", "clubs", "categories")),
        ("college", ("id", "participations", "students", "activities")),
    ):
        assert _select(service.ranking(dimension, limit=10), fields) == benchmark_simple_ranking(
            statistics_connection, dimension, 10
        )


def test_all_distributions_match_independent_sql(statistics_connection: Connection) -> None:
    service = StatisticsService(statistics_connection)
    fields = ("id", "activities", "participations", "students")
    for dimension in ("category", "college", "campus"):
        assert _select(service.distribution(dimension), fields) == benchmark_distribution(
            statistics_connection, dimension
        )
