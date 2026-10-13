from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.core.dependencies import get_embedding_client
from app.main import create_app
from tests.fakes.fake_embedding_client import FakeEmbeddingClient
from tests.sample_data import ATLAS_DIR, TEST_FILES_DIR


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = create_app()
    app.dependency_overrides[get_embedding_client] = lambda: FakeEmbeddingClient(dimensions=768)
    with TestClient(app) as test_client:
        yield test_client


def _upload(client: TestClient, topic_id: int, path_name: str, folder=ATLAS_DIR):  # type: ignore[no-untyped-def]
    path = folder / path_name
    return client.post(
        f"/api/v1/topics/{topic_id}/meetings", files={"file": (path.name, path.read_bytes())}
    )


def test_upload_flow_when_five_meetings_lists_them_in_date_order(client: TestClient) -> None:
    topic_id = client.post("/api/v1/topics", json={"name": "Project Atlas"}).json()["id"]
    for path in sorted(ATLAS_DIR.iterdir(), reverse=True):
        assert _upload(client, topic_id, path.name).status_code == 201

    meetings = client.get(f"/api/v1/topics/{topic_id}/meetings").json()
    assert [m["meeting_date"] for m in meetings] == sorted(m["meeting_date"] for m in meetings)
    assert len(meetings) == 5
    assert "Hussnain Razaq" in client.get(f"/api/v1/topics/{topic_id}/speakers").json()

    transcript = client.get(f"/api/v1/meetings/{meetings[0]['id']}/transcript").json()
    assert transcript["lines"][0]["line_number"] == 1
    assert client.get(f"/api/v1/topics/{topic_id}").json()["meeting_count"] == 5


def test_upload_flow_when_duplicate_or_bad_file_returns_clear_errors(client: TestClient) -> None:
    topic_id = client.post("/api/v1/topics", json={"name": "Atlas"}).json()["id"]
    assert _upload(client, topic_id, "2026-09-28_kickoff.vtt").status_code == 201

    duplicate = _upload(client, topic_id, "2026-09-28_kickoff.vtt")
    assert duplicate.status_code == 409
    assert "already uploaded" in duplicate.json()["message"]

    for name in ("empty-meeting.txt", "not-a-transcript.csv", "corrupt-meeting.docx"):
        response = _upload(client, topic_id, name, TEST_FILES_DIR)
        assert response.status_code == 400
        assert response.json()["message"]

    assert client.get(f"/api/v1/topics/{topic_id}").json()["meeting_count"] == 1
    assert client.get("/api/v1/topics/999/meetings").status_code == 404
