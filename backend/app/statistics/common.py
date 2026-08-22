from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any


def round_rate(value: Any) -> float | None:
    if value is None:
        return None
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def month_key(value: date | datetime) -> str:
    return value.strftime("%Y-%m")


def month_range(start: date | datetime, end: date | datetime) -> list[str]:
    cursor = date(start.year, start.month, 1)
    boundary = date(end.year, end.month, 1)
    if end.date() if isinstance(end, datetime) else end > boundary:
        boundary = date(boundary.year + (boundary.month == 12), boundary.month % 12 + 1, 1)
    result: list[str] = []
    while cursor < boundary:
        result.append(month_key(cursor))
        cursor = date(cursor.year + (cursor.month == 12), cursor.month % 12 + 1, 1)
    return result


def fill_months(
    rows: Iterable[dict[str, Any]],
    *,
    start: date | datetime,
    end: date | datetime,
    value_fields: tuple[str, ...],
) -> list[dict[str, Any]]:
    indexed = {str(row["month"]): dict(row) for row in rows}
    return [
        {"month": key, **{field: indexed.get(key, {}).get(field, 0) for field in value_fields}}
        for key in month_range(start, end)
    ]
