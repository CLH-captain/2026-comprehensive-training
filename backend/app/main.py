from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.activities import router as activities_router
from app.api.auth import router as auth_router
from app.api.clubs import router as clubs_router
from app.api.dictionaries import router as dictionaries_router
from app.api.health import router as health_router
from app.api.participation import router as participation_router
from app.api.statistics import router as statistics_router
from app.api.students import router as students_router
from app.core.config import Settings, get_settings
from app.core.errors import install_exception_handlers
from app.db.session import create_engine_from_url


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()
    app = FastAPI(title=resolved_settings.app_name)
    app.state.settings = resolved_settings
    app.state.engine = create_engine_from_url(resolved_settings.database_url)
    install_exception_handlers(app)

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        request.state.request_id = request.headers.get("X-Request-ID") or uuid4().hex
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[resolved_settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(activities_router, prefix="/api")
    app.include_router(auth_router, prefix="/api")
    app.include_router(clubs_router, prefix="/api")
    app.include_router(dictionaries_router, prefix="/api")
    app.include_router(health_router, prefix="/api")
    app.include_router(participation_router, prefix="/api")
    app.include_router(students_router, prefix="/api")
    app.include_router(statistics_router, prefix="/api")
    return app