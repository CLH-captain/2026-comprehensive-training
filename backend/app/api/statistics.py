from typing import Annotated

from fastapi import APIRouter, Query, Request

from app.services.statistics import StatisticsService

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get("/dashboard")
def dashboard(
    request: Request,
    term_id: Annotated[int | None, Query(ge=1)] = None,
    campus_id: Annotated[int | None, Query(ge=1)] = None,
) -> dict:
    with request.app.state.engine.connect() as connection:
        return StatisticsService(connection).dashboard(term_id=term_id, campus_id=campus_id)
