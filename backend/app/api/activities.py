from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Path, Query, Request

from app.services.activities import ActivityService

router = APIRouter(prefix="/activities", tags=["activities"])


@router.get("")
def list_activities(
    request: Request,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 15,
    search: Annotated[str | None, Query(max_length=200)] = None,
    term_id: Annotated[int | None, Query(ge=1)] = None,
    category_id: Annotated[int | None, Query(ge=1)] = None,
    club_id: Annotated[int | None, Query(ge=1)] = None,
    campus_id: Annotated[int | None, Query(ge=1)] = None,
    status: Literal["draft", "published", "completed", "cancelled"] | None = None,
) -> dict:
    with request.app.state.engine.connect() as connection:
        return ActivityService(connection).list_activities(
            page=page,
            page_size=page_size,
            search=search,
            term_id=term_id,
            category_id=category_id,
            club_id=club_id,
            campus_id=campus_id,
            status=status,
        )


@router.get("/{activity_id}")
def activity_detail(activity_id: Annotated[int, Path(ge=1)], request: Request) -> dict:
    with request.app.state.engine.connect() as connection:
        activity = ActivityService(connection).get_activity(activity_id)
    if activity is None:
        raise HTTPException(status_code=404, detail="Activity not found")
    return activity
