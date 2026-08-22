from __future__ import annotations

from typing import Any

from sqlalchemy import Connection, text

from app.statistics.distributions import DistributionDimension, distribution
from app.statistics.filters import StatisticsFilter
from app.statistics.overview import overview
from app.statistics.rankings import RankingDimension, ranking
from app.statistics.summaries import club_summary, student_summary
from app.statistics.trends import monthly_trend


class StatisticsService:
    """Single statistics facade used by HTTP routes and future Agent tools."""

    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def overview(self, filters: StatisticsFilter | None = None) -> dict[str, Any]:
        return overview(self.connection, filters or StatisticsFilter())

    def monthly_trend(self, filters: StatisticsFilter | None = None) -> list[dict[str, Any]]:
        return monthly_trend(self.connection, filters or StatisticsFilter())

    def ranking(
        self,
        dimension: RankingDimension,
        filters: StatisticsFilter | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        return ranking(self.connection, filters or StatisticsFilter(), dimension, limit)

    def distribution(
        self,
        dimension: DistributionDimension,
        filters: StatisticsFilter | None = None,
    ) -> list[dict[str, Any]]:
        return distribution(self.connection, filters or StatisticsFilter(), dimension)

    def student_summary(
        self,
        student_id: int,
        filters: StatisticsFilter | None = None,
    ) -> dict[str, Any] | None:
        return student_summary(self.connection, student_id, filters)

    def club_summary(
        self,
        club_id: int,
        filters: StatisticsFilter | None = None,
    ) -> dict[str, Any] | None:
        return club_summary(self.connection, club_id, filters)

    def dashboard(self, filters: StatisticsFilter | None = None) -> dict[str, Any]:
        filters = filters or StatisticsFilter()
        contexts = {
            "terms": [
                dict(row)
                for row in self.connection.execute(
                    text("SELECT id, name, is_default FROM academic_terms ORDER BY start_date")
                ).mappings()
            ],
            "campuses": [
                dict(row)
                for row in self.connection.execute(
                    text("SELECT id, name FROM campuses WHERE is_active = 1 ORDER BY id")
                ).mappings()
            ],
        }
        return {
            "overview": self.overview(filters),
            "monthly_trend": self.monthly_trend(filters),
            "club_ranking": self.ranking("club", filters, 8),
            "college_ranking": self.ranking("college", filters, 8),
            "category_distribution": self.distribution("category", filters),
            "top_activities": self.ranking("activity", filters, 6),
            "contexts": contexts,
        }
