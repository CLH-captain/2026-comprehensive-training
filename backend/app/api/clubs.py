from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Path, Query, Request

from app.api.dependencies import AuthorizedScope
from app.core.permissions import require_role
from app.schemas.business import ClubCreate, ClubUpdate, MembershipUpsert
from app.services.clubs import ClubService
from app.services.crud import CrudService

router = APIRouter(prefix="/clubs", tags=["clubs"])


@router.get("")
def list_clubs(
    request: Request,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 15,
    search: Annotated[str | None, Query(max_length=100)] = None,
    category_id: Annotated[int | None, Query(ge=1)] = None,
    campus_id: Annotated[int | None, Query(ge=1)] = None,
    status: Literal["active", "inactive"] | None = None,
) -> dict:
    with request.app.state.engine.connect() as connection:
        return ClubService(connection).list_clubs(
            page=page,
            page_size=page_size,
            search=search,
            category_id=category_id,
            campus_id=campus_id,
            status=status,
        )


@router.get("/{club_id}")
def club_detail(club_id: Annotated[int, Path(ge=1)], request: Request) -> dict:
    with request.app.state.engine.connect() as connection:
        club = ClubService(connection).get_club(club_id)
    if club is None:
        raise HTTPException(status_code=404, detail="Club not found")
    return club


@router.post("", status_code=201)
def create_club(payload: ClubCreate, request: Request, scope: AuthorizedScope) -> dict:
    require_role(scope, "admin")
    with request.app.state.engine.begin() as connection:
        return CrudService(connection).create_club(payload.model_dump())


@router.put("/{club_id}")
def update_club(
    club_id: Annotated[int, Path(ge=1)], payload: ClubUpdate,
    request: Request, scope: AuthorizedScope,
) -> dict:
    require_role(scope, "admin", "club_manager")
    scope.require_club(club_id)
    with request.app.state.engine.begin() as connection:
        return CrudService(connection).update_club(
            club_id, payload.model_dump(exclude_unset=True)
        )


@router.delete("/{club_id}", status_code=204)
def delete_club(
    club_id: Annotated[int, Path(ge=1)], request: Request, scope: AuthorizedScope
) -> None:
    require_role(scope, "admin")
    with request.app.state.engine.begin() as connection:
        CrudService(connection).deactivate_club(club_id)


@router.get("/{club_id}/members")
def list_members(
    club_id: Annotated[int, Path(ge=1)], request: Request, scope: AuthorizedScope
) -> dict:
    require_role(scope, "admin", "club_manager")
    scope.require_club(club_id)
    with request.app.state.engine.connect() as connection:
        items = CrudService(connection).list_memberships(club_id)
    return {"items": items, "total": len(items)}


@router.put("/{club_id}/members")
def upsert_member(
    club_id: Annotated[int, Path(ge=1)], payload: MembershipUpsert,
    request: Request, scope: AuthorizedScope,
) -> dict:
    require_role(scope, "admin", "club_manager")
    scope.require_club(club_id)
    with request.app.state.engine.begin() as connection:
        return CrudService(connection).upsert_membership(club_id, payload.model_dump())