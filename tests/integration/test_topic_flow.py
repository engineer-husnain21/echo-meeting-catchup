from fastapi.testclient import TestClient

from app.main import create_app


def test_topic_flow_when_created_then_listed_and_fetched() -> None:
    with TestClient(create_app()) as client:
        created = client.post("/api/v1/topics", json={"name": "Project Atlas"})
        assert created.status_code == 201
        topic_id = created.json()["id"]

        assert [t["name"] for t in client.get("/api/v1/topics").json()] == ["Project Atlas"]
        assert client.get(f"/api/v1/topics/{topic_id}").json()["meeting_count"] == 0

        duplicate = client.post("/api/v1/topics", json={"name": "Project Atlas"})
        assert duplicate.status_code == 409
        assert client.get("/api/v1/topics/999").status_code == 404
