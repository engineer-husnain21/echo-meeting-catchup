from fastapi.testclient import TestClient

from app.main import create_app


def test_web_flow_when_root_opened_serves_ui_and_api_still_works() -> None:
    with TestClient(create_app()) as client:
        page = client.get("/")
        assert page.status_code == 200
        assert "<title>ECHO" in page.text
        assert client.get("/app.js").status_code == 200
        assert client.get("/api/v1/health").status_code == 200
        assert client.get("/api/v1/topics").json() == []
