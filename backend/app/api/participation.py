from typing import Annotated

from fastapi import APIRouter, Path, Query, Request

from app.api.dependencies import AuthorizedScope
from app.core.permissions import require_role
from app.schemas.business import (
    AttendanceUpsert,
    RegistrationCreate,
    RegistrationStatusUpdate,
)
from app.services.crud import CrudService

router = APIRouter(tags=["participation"])


@router.get("/registrations")
def list_registrations(
    request: Request,
    scope: AuthorizedScope,
    activity_id: Annotated[int | None, Query(ge=1)] = None,
    student_id: Annotated[int | None, Query(ge=1)] = None,
) -> dict:
    if scope.role == "student":
        student_id = scope.student_id
    with request.app.state.engine.connect() as connection:
        service = CrudService(connection)
        if activity_id is not None and scope.role == "club_manager":
            scope.require_club(service.activity_club_id(activity_id))
        items = service.list_participation_records(
            "activity_registrations", activity_id=activity_id, student_id=student_id,
            club_ids=scope.club_ids if scope.role == "club_manager" else None,
        )
    return {"items": items, "total": len(items)}


@router.post("/registrations", status_code=201)
def create_registration(
    payload: RegistrationCreate, request: Request, scope: AuthorizedScope
) -> dict:
    with request.app.state.engine.begin() as connection:
        service = CrudService(connection)
        if scope.role == "student":
            scope.require_student(payload.student_id)
        elif scope.role == "club_manager":
            scope.require_club(service.activity_club_id(payload.activity_id))
        else:
            require_role(scope, "admin")
        return service.create_registration(payload.model_dump())


@router.patch("/registrations/{registration_id}")
def update_registration(
    registration_id: Annotated[int, Path(ge=1)],
    payload: RegistrationStatusUpdate,
    request: Request,
    scope: AuthorizedScope,
) -> dict:
    with request.app.state.engine.begin() as connection:
        service = CrudService(connection)
        student_id, club_id = service.registration_owner(registration_id)
        if scope.role == "student":
            scope.require_student(student_id)
            if payload.status != "cancelled":
                require_role(scope, "admin")
        elif scope.role == "club_manager":
            scope.require_club(club_id)
        else:
            require_role(scope, "admin")
        return service.update_registration(registration_id, payload.status)


@router.get("/attendance")
def list_attendance(
    request: Request,
    scope: AuthorizedScope,
    activity_id: Annotated[int | None, Query(ge=1)] = None,
    student_id: Annotated[int | None, Query(ge=1)] = None,
) -> dict:
    if scope.role == "student":
        student_id = scope.student_id
    with request.app.state.engine.connect() as connection:
        service = CrudService(connection)
        if activity_id is not None and scope.role == "club_manager":
            scope.require_club(service.activity_club_id(activity_id))
        items = service.list_participation_records(
            "activity_attendance", activity_id=activity_id, student_id=student_id,
            club_ids=scope.club_ids if scope.role == "club_manager" else None,
        )
    return {"items": items, "total": len(items)}


@router.put("/attendance")
def upsert_attendance(
    payload: AttendanceUpsert, request: Request, scope: AuthorizedScope
) -> dict:
    require_role(scope, "admin", "club_manager")
    with request.app.state.engine.begin() as connection:
        service = CrudService(connection)
        scope.require_club(service.activity_club_id(payload.activity_id))
        return service.upsert_attendance(payload.model_dump())
