from sqlalchemy import Connection

from app.statistics.distributions import distribution
from app.statistics.filters import StatisticsFilter
from app.statistics.overview import overview
from app.statistics.trends import monthly_trend


def test_full_dataset_overview(statistics_connection: Connection) -> None:
    result = overview(statistics_connection, StatisticsFilter())

    assert result == {
        "active_clubs": 45,
        "completed_activities": 313,
        "registrations": 19979,
        "participations": 16028,
        "active_students": 2984,
        "attendance_rate": 80.22,
    }


def test_term_trend_fills_every_month(statistics_connection: Connection) -> None:
    result = monthly_trend(statistics_connection, StatisticsFilter(term_id=2))

    assert [row["month"] for row in result] == [
        "2026-02",
        "2026-03",
        "2026-04",
        "2026-05",
        "2026-06",
        "2026-07",
    ]
    assert all(set(row) == {"month", "activities", "participations", "active_students"} for row in result)


def test_distributions_cover_all_dimensions(statistics_connection: Connection) -> None:
    filters = StatisticsFilter()

    categories = distribution(statistics_connection, filters, "category")
    colleges = distribution(statistics_connection, filters, "college")
    campuses = distribution(statistics_connection, filters, "campus")

    assert len(categories) == 7
    assert len(colleges) == 12
    assert len(campuses) == 2
    assert sum(row["participations"] for row in categories) == 16028
    assert sum(row["participations"] for row in colleges) == 16028
    assert sum(row["participations"] for row in campuses) == 16028
