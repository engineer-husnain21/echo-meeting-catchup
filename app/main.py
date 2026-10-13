"""App setup: registers middlewares and routers. No business logic here."""

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.middlewares.error_handler_middleware import ErrorHandlerMiddleware
from app.middlewares.logging_middleware import LoggingMiddleware
from app.middlewares.request_id_middleware import RequestIdMiddleware
from app.routers import health_router


def create_app() -> FastAPI:
    """Build the FastAPI application."""
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(title=settings.app_name, version="0.1.0")

    # Starlette runs the last added middleware first, so RequestId runs outermost.
    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RequestIdMiddleware)

    app.include_router(health_router.router)
    return app


app = create_app()
