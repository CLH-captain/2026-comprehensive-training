from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request

from app.statistics.filters import StatisticsFilter
from app.statistics.service import StatisticsService

router = APIRouter(prefix="/statistics", tags=["statistics"])


def statistics_filter(
    term_id: Annotated[int | None, Query(ge=1)] = None,
    campus_id: Annotated[int | None, Query(ge=1)] = None,
    college_id: Annotated[int | None, Query(ge=1)] = None,
    filter_club_id: Annotated[int | None, Query(alias="club_id", ge=1)] = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> StatisticsFilter:
    try:
        return StatisticsFilter(
            term_id=term_id,
            campus_id=campus_id,
            college_id=college_id,
            club_id=filter_club_id,
            date_from=date_from,
            date_to=date_to,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc




@router.get("/dashboard")
def dashboard(
    request: Request,
    filters: Annotated[StatisticsFilter, Depends(statistics_filter)],
) -> dict:
    with request.app.state.engine.connect() as connection:
        return StatisticsService(connection).dashboard(filters)


@router.get("/overview")
def statistics_overview(
    request: Request,
    filters: Annotated[StatisticsFilter, Depends(statistics_filter)],
) -> dict:
    with request.app.state.engine.connect() as connection:
        return StatisticsService(connection).overview(filters)


@router.get("/trends/monthly")
def statistics_monthly_trend(
    request: Request,
    filters: Annotated[StatisticsFilter, Depends(statistics_filter)],
) -> list[dict]:
    with request.app.state.engine.connect() as connection:
        return StatisticsService(connection).monthly_trend(filters)


@router.get("/rankings/{dimension}")
def statistics_ranking(
    dimension: Annotated[Literal["club", "activity", "student", "college"], Path()],
    request: Request,
    filters: Annotated[StatisticsFilter, Depends(statistics_filter)],
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> list[dict]:
    with request.app.state.engine.connect() as connection:
        return StatisticsService(connection).ranking(dimension, filters, limit)


@router.get("/distributions/{dimension}")
def statistics_distribution(
    dimension: Annotated[Literal["category", "college", "campus"], Path()],
    request: Request,
    filters: Annotated[StatisticsFilter, Depends(statistics_filter)],
) -> list[dict]:
    with request.app.state.engine.connect() as connection:
        return StatisticsService(connection).distribution(dimension, filters)


@router.get("/students/{student_id}")
def statistics_student_summary(
    student_id: Annotated[int, Path(ge=1)],
    request: Request,
    filters: Annotated[StatisticsFilter, Depends(statistics_filter)],
) -> dict:
    with request.app.state.engine.connect() as connection:
        result = StatisticsService(connection).student_summary(student_id, filters)
    if result is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return result


@router.get("/clubs/{club_id}")
def statistics_club_summary(
    club_id: Annotated[int, Path(ge=1)],
    request: Request,
    filters: Annotated[StatisticsFilter, Depends(statistics_filter)],
) -> dict:
    with request.app.state.engine.connect() as connection:
        result = StatisticsService(connection).club_summary(club_id, filters)
    if result is None:
        raise HTTPException(status_code=404, detail="Club not found")
    return result