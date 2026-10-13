from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.dependencies import get_app_settings
from app.routers import health_router


def test_get_health_when_called_returns_ok() -> None:
    app = FastAPI()
    app.include_router(health_router.router)
    app.dependency_overrides[get_app_settings] = lambda: Settings(_env_file=None, app_name="TEST")  # type: ignore[call-arg]
    response = TestClient(app).get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "app_name": "TEST"}
