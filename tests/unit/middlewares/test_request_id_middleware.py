from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middlewares.request_id_middleware import REQUEST_ID_HEADER, RequestIdMiddleware


def _build_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestIdMiddleware)

    @app.get("/ping")
    async def ping() -> dict[str, str]:
        return {"ok": "yes"}

    return app


def test_dispatch_when_no_header_creates_request_id() -> None:
    response = TestClient(_build_app()).get("/ping")
    assert response.headers[REQUEST_ID_HEADER]


def test_dispatch_when_header_given_echoes_it() -> None:
    response = TestClient(_build_app()).get("/ping", headers={REQUEST_ID_HEADER: "abc"})
    assert response.headers[REQUEST_ID_HEADER] == "abc"
