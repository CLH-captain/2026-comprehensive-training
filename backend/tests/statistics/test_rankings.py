import pytest
from sqlalchemy import Connection

from app.statistics.common import round_rate
from app.statistics.filters import StatisticsFilter
from app.statistics.rankings import club_ranking, ranking


def test_club_ranking_is_stable_and_scored(statistics_connection: Connection) -> None:
    rows = club_ranking(statistics_connection, StatisticsFilter(), limit=45)

    assert len(rows) == 45
    maxima = {key: max(row[key] for row in rows) for key in ("activities", "participations", "students")}
    first = rows[0]
    expected = round_rate(
        0.5 * first["activities"] / maxima["activities"] * 100
        + 0.3 * first["participations"] / maxima["participations"] * 100
        + 0.2 * first["students"] / maxima["students"] * 100
    )
    assert first["activity_score"] == expected
    assert all(0 <= row["activity_score"] <= 100 for row in rows)
    assert rows == sorted(rows, key=lambda row: (-row["activity_score"], row["name"], row["id"]))


def test_all_ranking_dimensions_return_requested_limit(statistics_connection: Connection) -> None:
    filters = StatisticsFilter()
    for dimension in ("club", "activity", "student", "college"):
        assert len(ranking(statistics_connection, filters, dimension, limit=5)) == 5


def test_ranking_limit_is_bounded(statistics_connection: Connection) -> None:
    with pytest.raises(ValueError, match="between 1 and 100"):
        club_ranking(statistics_connection, StatisticsFilter(), limit=101)
