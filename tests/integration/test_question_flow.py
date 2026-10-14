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
            files = {"file": (path.name, path.read_bytes())}
            client.post(f"/api/v1/topics/{topic_id}/meetings", files=files)
        yield client, llm, topic_id


def test_question_flow_when_board_built_answers_from_board_with_db_quotes(setup) -> None:  # type: ignore[no-untyped-def]
    client, llm, topic_id = setup
    llm.replies = [*extractor_replies(), stance_reply(), timeline_reply()]
    client.post(f"/api/v1/topics/{topic_id}/board/refresh")
    llm.calls.clear()
    llm.replies = [
        {
            "status": "answered",
            "answer": "MongoDB. It was PostgreSQL at the kickoff, then changed on October 5.",
            "citations": [{"meeting_id": 3, "line": 7}],
        }
    ]

    response = client.post(
        f"/api/v1/topics/{topic_id}/questions",
        json={"question": "Which database are we using?", "user_name": "Hussnain Razaq"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "answered"
    assert body["citations"][0]["meeting_title"] == "Data model review"
    assert "MongoDB" in body["citations"][0]["text"]
    assert body["elapsed_ms"] >= 0
    assert "decision | database choice | now: Switch to MongoDB." in llm.calls[0][1]


def test_question_flow_when_question_blank_returns_400(setup) -> None:  # type: ignore[no-untyped-def]
    client, llm, topic_id = setup
    response = client.post(f"/api/v1/topics/{topic_id}/questions", json={"question": "   "})
    assert response.status_code == 422
    assert llm.calls == []


def test_question_flow_when_llm_down_returns_503(setup) -> None:  # type: ignore[no-untyped-def]
    client, llm, topic_id = setup
    llm.fail = True
    response = client.post(f"/api/v1/topics/{topic_id}/questions", json={"question": "Hi?"})
    assert response.status_code == 503
    assert "not available" in response.json()["message"]


def test_question_flow_when_topic_missing_returns_404(setup) -> None:  # type: ignore[no-untyped-def]
    client, _, _ = setup
    response = client.post("/api/v1/topics/999/questions", json={"question": "Hi?"})
    assert response.status_code == 404
