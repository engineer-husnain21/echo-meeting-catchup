"""App setup: registers middlewares and routers. No business logic here."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.dependencies import get_database
from app.core.logging import configure_logging
from app.middlewares.error_handler_middleware import ErrorHandlerMiddleware
from app.middlewares.logging_middleware import LoggingMiddleware
from app.middlewares.request_id_middleware import RequestIdMiddleware
from app.routers import (
    board_router,
    health_router,
    meeting_router,
    question_router,
    topic_router,
)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Create tables on startup and close the DB on shutdown."""
    database = get_database()
    await database.create_tables()
    yield
    await database.dispose()


def create_app() -> FastAPI:
    """Build the FastAPI application."""
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

    # Starlette runs the last added middleware first, so RequestId runs outermost.
    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RequestIdMiddleware)

    app.include_router(health_router.router)
    app.include_router(topic_router.router)
    app.include_router(meeting_router.router)
    app.include_router(board_router.router)
    app.include_router(question_router.router)
    return app


app = create_app()
