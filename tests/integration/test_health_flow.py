from fastapi.testclient import TestClient

from app.main import create_app
from app.middlewares.request_id_middleware import REQUEST_ID_HEADER


def test_health_flow_when_full_app_runs_returns_ok_with_request_id() -> None:
    response = TestClient(create_app()).get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.headers[REQUEST_ID_HEADER]
