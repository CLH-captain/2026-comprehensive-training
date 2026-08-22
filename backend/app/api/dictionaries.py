from typing import Annotated, Literal

from fastapi import APIRouter, Body, Path, Request
from pydantic import ValidationError

from app.api.dependencies import AuthorizedScope
from app.core.errors import AppError
from app.core.permissions import require_role
from app.schemas.business import (
    CampusCreate,
    CollegeCreate,
    DictionaryCreate,
    MajorCreate,
    TermCreate,
    VenueCreate,
)
from app.services.crud import CrudService

router = APIRouter(prefix="/dictionaries", tags=["dictionaries"])
Resource = Literal[
    "campuses",
    "terms",
    "colleges",
    "majors",
    "club-categories",
    "activity-categories",
    "venues",
]
MODELS = {
    "campuses": CampusCreate,
    "terms": TermCreate,
    "colleges": CollegeCreate,
    "majors": MajorCreate,
    "club-categories": DictionaryCreate,
    "activity-categories": DictionaryCreate,
    "venues": VenueCreate,
}


def validate_payload(resource: str, payload: dict) -> dict:
    try:
        return MODELS[resource].model_validate(payload).model_dump()
    except ValidationError as exc:
        raise AppError(422, "VALIDATION_ERROR", str(exc)) from exc


@router.get("/{resource}")
def list_dictionary(resource: Resource, request: Request) -> dict:
    with request.app.state.engine.connect() as connection:
        items = CrudService(connection).list_dictionary(resource)
    return {"items": items, "total": len(items)}


@router.post("/{resource}", status_code=201)
def create_dictionary(
    resource: Resource,
    payload: Annotated[dict, Body()],
    request: Request,
    scope: AuthorizedScope,
) -> dict:
    require_role(scope, "admin")
    with request.app.state.engine.begin() as connection:
        return CrudService(connection).create_dictionary(
            resource, validate_payload(resource, payload)
        )


@router.put("/{resource}/{record_id}")
def update_dictionary(
    resource: Resource,
    record_id: Annotated[int, Path(ge=1)],
    payload: Annotated[dict, Body()],
    request: Request,
    scope: AuthorizedScope,
) -> dict:
    require_role(scope, "admin")
    with request.app.state.engine.begin() as connection:
        return CrudService(connection).update_dictionary(
            resource, record_id, validate_payload(resource, payload)
        )


@router.delete("/{resource}/{record_id}", status_code=204)
def delete_dictionary(
    resource: Resource,
    record_id: Annotated[int, Path(ge=1)],
    request: Request,
    scope: AuthorizedScope,
) -> None:
    require_role(scope, "admin")
    with request.app.state.engine.begin() as connection:
        CrudService(connection).deactivate_dictionary(resource, record_id)
