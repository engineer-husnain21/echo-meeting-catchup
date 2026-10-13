"""Global error handler: turns exceptions into clean JSON responses."""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.exceptions import EchoError
from app.core.logging import get_logger

_logger = get_logger("errors")


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Catches EchoError and unexpected errors so the app keeps running."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = getattr(request.state, "request_id", None)
        try:
            return await call_next(request)
        except EchoError as error:
            _logger.warning("%s: %s", error.error_code, error.message)
            return JSONResponse(
                status_code=error.status_code,
                content={
                    "error": error.error_code,
                    "message": error.message,
                    "request_id": request_id,
                },
            )
        except Exception:
            _logger.exception("Unhandled error on %s", request.url.path)
            return JSONResponse(
                status_code=500,
                content={
                    "error": "internal_error",
                    "message": "Something went wrong. Please try again.",
                    "request_id": request_id,
                },
            )
