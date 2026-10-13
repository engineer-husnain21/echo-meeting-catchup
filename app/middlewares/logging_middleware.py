"""Logs method, path, status and duration for every request."""

import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger

_logger = get_logger("http")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Writes one log line per request."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - started) * 1000
        request_id = getattr(request.state, "request_id", "-")
        _logger.info(
            "%s %s -> %s in %.1f ms (request_id=%s)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            request_id,
        )
        return response
