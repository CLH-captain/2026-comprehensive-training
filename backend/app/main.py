from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.clubs import router as clubs_router
from app.api.health import router as health_router
from app.api.statistics import router as statistics_router
from app.api.students import router as students_router
from app.core.config import Settings, get_settings
from app.db.session import create_engine_from_url


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()
    app = FastAPI(title=resolved_settings.app_name)
    app.state.settings = resolved_settings
    app.state.engine = create_engine_from_url(resolved_settings.database_url)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[resolved_settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(clubs_router, prefix="/api")
    app.include_router(health_router, prefix="/api")
    app.include_router(students_router, prefix="/api")
    app.include_router(statistics_router, prefix="/api")
    return app
