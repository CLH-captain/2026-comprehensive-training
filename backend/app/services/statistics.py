"""Compatibility import for callers created before the statistics package split."""

from app.statistics.service import StatisticsService

__all__ = ["StatisticsService"]