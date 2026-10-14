from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.core.dependencies import get_embedding_client, get_llm_client
from app.main import create_app
from tests.fakes.board_replies import extractor_replies, stance_reply, timeline_reply
from tests.fakes.fake_embedding_client import FakeEmbeddingClient
from tests.fakes.fake_llm_client import FakeLlmClient
from tests.sample_data import ATLAS_DIR


@pytest.fixture
def setup() -> Iterator[tuple[TestClient, FakeLlmClient, int]]:
    llm = FakeLlmClient()
    app = create_app()
    app.dependency_overrides[get_embedding_client] = lambda: FakeEmbeddingClient(dimensions=768)
    app.dependency_overrides[get_llm_client] = lambda: llm
    with TestClient(app) as client:
        topic_id = client.post("/api/v1/topics", json={"name": "Atlas"}).json()["id"]
        for path in sorted(ATLAS_DIR.iterdir()):
            client.post(
                f"/api/v1/topics/{topic_id}/meetings",
                files={"file": (path.name, path.read_bytes())},
            )
        yield client, llm, topic_id


def test_briefing_flow_when_board_missing_returns_404_without_llm(setup) -> None:  # type: ignore[no-untyped-def]
    client, llm, topic_id = setup
    response = client.post(f"/api/v1/topics/{topic_id}/briefing", json={})
    assert response.status_code == 404
    assert "not been built" in response.json()["message"]
    assert llm.calls == []


def test_briefing_flow_when_board_built_returns_grounded_briefing(setup) -> None:  # type: ignore[no-untyped-def]
    client, llm, topic_id = setup
    llm.replies = [*extractor_replies(), stance_reply(), timeline_reply()]
    client.post(f"/api/v1/topics/{topic_id}/board/refresh")
    llm.calls.clear()
    llm.replies = [
        {
            "briefing": "Here's where things stand. The team moved from PostgreSQL to MongoDB.",
            "citations": ["M3 L7", "M1 L15", "M2 L1"],  # M2 L1 is not on the board
        }
    ]
    response = client.post(
        f"/api/v1/topics/{topic_id}/briefing", json={"user_name": "Hussnain Razaq"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["briefing"].startswith("Here's where things stand.")
    assert [(q["meeting_id"], q["line"]) for q in body["citations"]] == [(3, 7), (1, 15)]
    assert "Listener: Hussnain Razaq" in llm.calls[0][1]


def test_briefing_flow_when_llm_returns_nothing_returns_404(setup) -> None:  # type: ignore[no-untyped-def]
    client, llm, topic_id = setup
    llm.replies = [*extractor_replies(), stance_reply(), timeline_reply()]
    client.post(f"/api/v1/topics/{topic_id}/board/refresh")
    llm.replies = [{}]
    response = client.post(f"/api/v1/topics/{topic_id}/briefing", json={})
    assert response.status_code == 404
