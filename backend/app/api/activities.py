from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Path, Query, Request

from app.api.dependencies import AuthorizedScope
from app.core.permissions import require_role
from app.schemas.business import ActivityCreate, ActivityUpdate
from app.services.activities import ActivityService
from app.services.crud import CrudService

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


@router.post("", status_code=201)
def create_activity(
    payload: ActivityCreate, request: Request, scope: AuthorizedScope
) -> dict:
    require_role(scope, "admin", "club_manager")
    scope.require_club(payload.club_id)
    with request.app.state.engine.begin() as connection:
        return CrudService(connection).create_activity(payload.model_dump())


@router.put("/{activity_id}")
def update_activity(
    activity_id: Annotated[int, Path(ge=1)], payload: ActivityUpdate,
    request: Request, scope: AuthorizedScope,
) -> dict:
    require_role(scope, "admin", "club_manager")
    with request.app.state.engine.begin() as connection:
        service = CrudService(connection)
        scope.require_club(service.activity_club_id(activity_id))
        return service.update_activity(
            activity_id, payload.model_dump(exclude_unset=True)
        )


@router.delete("/{activity_id}")
def delete_activity(
    activity_id: Annotated[int, Path(ge=1)], request: Request,
    scope: AuthorizedScope,
) -> dict:
    require_role(scope, "admin", "club_manager")
    with request.app.state.engine.begin() as connection:
        service = CrudService(connection)
        scope.require_club(service.activity_club_id(activity_id))
        return {"result": service.delete_activity(activity_id)}