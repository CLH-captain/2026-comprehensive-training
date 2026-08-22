from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Path, Query, Request

from app.services.clubs import ClubService

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
