from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.api.agent_dependencies import get_agent_scope
from app.core.errors import AppError
from app.core.permissions import AccessScope
from app.statistics.filters import StatisticsFilter
from app.statistics.service import StatisticsService

router = APIRouter(prefix="/internal/agent-tools", tags=["internal-agent-tools"])
AgentScope = Annotated[AccessScope, Depends(get_agent_scope)]


class ToolFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")
    term_id: int | None = Field(default=None, ge=1)
    campus_id: int | None = Field(default=None, ge=1)
    college_id: int | None = Field(default=None, ge=1)
    club_id: int | None = Field(default=None, ge=1)
    category_id: int | None = Field(default=None, ge=1)
    start_date: date | None = None
    end_date: date | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValueError("start_date must be earlier than end_date")
        return self

    def filters(self) -> StatisticsFilter:
        return StatisticsFilter(
            term_id=self.term_id,
            campus_id=self.campus_id,
            college_id=self.college_id,
            club_id=self.club_id,
            activity_category_id=self.category_id,
            date_from=self.start_date,
            date_to=self.end_date,
        )


class ClubRankingInput(ToolFilters):
    metric: Literal["activity_score"] = "activity_score"
    limit: int = Field(default=10, ge=1, le=50)


class ActivityRankingInput(ToolFilters):
    metric: Literal["participant_times"] = "participant_times"
    limit: int = Field(default=10, ge=1, le=50)


class TrendInput(ToolFilters):
    granularity: Literal["month"] = "month"
    metric: Literal["participant_times"] = "participant_times"


class DistributionInput(ToolFilters):
    dimension: Literal["category", "college", "campus"]
    metric: Literal["participant_times"] = "participant_times"


class StudentInput(ToolFilters):
    student_id: int | None = Field(default=None, ge=1)


class ClubInput(ToolFilters):
    club_id: int = Field(ge=1)


def scoped(scope: AccessScope, data: ToolFilters) -> StatisticsFilter:
    if scope.role == "club_manager":
        if data.club_id is None:
            raise AppError(
                403,
                "CLUB_SCOPE_REQUIRED",
                "Club managers must specify a managed club",
            )
        scope.require_club(data.club_id)
    return data.filters()


@router.post("/overview")
def overview(data: ToolFilters, request: Request, scope: AgentScope) -> dict:
    with request.app.state.engine.connect() as connection:
        return StatisticsService(connection).overview(scoped(scope, data))


@router.post("/club-ranking")
def club_ranking(
    data: ClubRankingInput, request: Request, scope: AgentScope
) -> list[dict]:
    with request.app.state.engine.connect() as connection:
        return StatisticsService(connection).ranking(
            "club", scoped(scope, data), data.limit
        )


@router.post("/activity-ranking")
def activity_ranking(
    data: ActivityRankingInput, request: Request, scope: AgentScope
) -> list[dict]:
    with request.app.state.engine.connect() as connection:
        return StatisticsService(connection).ranking(
            "activity", scoped(scope, data), data.limit
        )


@router.post("/trend")
def trend(data: TrendInput, request: Request, scope: AgentScope) -> list[dict]:
    with request.app.state.engine.connect() as connection:
        return StatisticsService(connection).monthly_trend(scoped(scope, data))


@router.post("/distribution")
def distribution(
    data: DistributionInput, request: Request, scope: AgentScope
) -> list[dict]:
    with request.app.state.engine.connect() as connection:
        return StatisticsService(connection).distribution(
            data.dimension, scoped(scope, data)
        )


@router.post("/student-summary")
def student_summary(
    data: StudentInput, request: Request, scope: AgentScope
) -> dict:
    if scope.role == "student":
        student_id = scope.student_id
    elif scope.is_admin:
        student_id = data.student_id
    else:
        student_id = None
    if student_id is None:
        raise AppError(
            403,
            "FORBIDDEN",
            "Student summary is limited to the student or an administrator",
        )
    with request.app.state.engine.connect() as connection:
        result = StatisticsService(connection).student_summary(
            student_id, data.filters()
        )
    if result is None:
        raise AppError(404, "STUDENT_NOT_FOUND", "Student not found")
    return result


@router.post("/club-summary")
def club_summary(data: ClubInput, request: Request, scope: AgentScope) -> dict:
    if scope.role == "club_manager":
        scope.require_club(data.club_id)
    with request.app.state.engine.connect() as connection:
        result = StatisticsService(connection).club_summary(
            data.club_id, data.filters()
        )
    if result is None:
        raise AppError(404, "CLUB_NOT_FOUND", "Club not found")
    return result