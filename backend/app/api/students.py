from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Path, Query, Request

from app.api.dependencies import AuthorizedScope
from app.core.permissions import require_role
from app.schemas.business import StudentCreate, StudentUpdate
from app.services.crud import CrudService
from app.services.students import StudentService

router = APIRouter(prefix="/students", tags=["students"])


@router.get("")
def list_students(
    request: Request,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[str | None, Query(max_length=50)] = None,
    college_id: Annotated[int | None, Query(ge=1)] = None,
    major_id: Annotated[int | None, Query(ge=1)] = None,
    grade_no: Annotated[int | None, Query(ge=1, le=4)] = None,
    status: Literal["active", "graduated", "suspended"] | None = None,
) -> dict:
    with request.app.state.engine.connect() as connection:
        return StudentService(connection).list_students(
            page=page,
            page_size=page_size,
            search=search,
            college_id=college_id,
            major_id=major_id,
            grade_no=grade_no,
            status=status,
        )


@router.get("/{student_id}")
def student_detail(student_id: Annotated[int, Path(ge=1)], request: Request) -> dict:
    with request.app.state.engine.connect() as connection:
        student = StudentService(connection).get_student(student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.post("", status_code=201)
def create_student(
    payload: StudentCreate, request: Request, scope: AuthorizedScope
) -> dict:
    require_role(scope, "admin")
    with request.app.state.engine.begin() as connection:
        return CrudService(connection).create_student(payload.model_dump())


@router.put("/{student_id}")
def update_student(
    student_id: Annotated[int, Path(ge=1)],
    payload: StudentUpdate,
    request: Request,
    scope: AuthorizedScope,
) -> dict:
    require_role(scope, "admin")
    with request.app.state.engine.begin() as connection:
        return CrudService(connection).update_student(
            student_id, payload.model_dump(exclude_unset=True)
        )


@router.delete("/{student_id}", status_code=204)
def delete_student(
    student_id: Annotated[int, Path(ge=1)], request: Request, scope: AuthorizedScope
) -> None:
    require_role(scope, "admin")
    with request.app.state.engine.begin() as connection:
        CrudService(connection).deactivate_student(student_id)