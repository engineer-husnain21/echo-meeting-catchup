from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.exceptions import NotFoundError
from app.middlewares.error_handler_middleware import ErrorHandlerMiddleware
from app.middlewares.request_id_middleware import RequestIdMiddleware


def _build_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(RequestIdMiddleware)

    @app.get("/missing")
    async def missing() -> None:
        raise NotFoundError("Topic not found")

    @app.get("/boom")
    async def boom() -> None:
        raise RuntimeError("unexpected")

    return app


def test_dispatch_when_echo_error_returns_mapped_status() -> None:
    response = TestClient(_build_app()).get("/missing")
    assert response.status_code == 404
    assert response.json()["error"] == "not_found"
    assert response.json()["request_id"]


def test_dispatch_when_unexpected_error_returns_500_without_details() -> None:
    response = TestClient(_build_app()).get("/boom")
    assert response.status_code == 500
    assert "unexpected" not in response.text
