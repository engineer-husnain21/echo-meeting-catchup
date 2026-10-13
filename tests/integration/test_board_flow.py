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
    llm = FakeLlmClient([*extractor_replies(), stance_reply(), timeline_reply()])
    app = create_app()
    app.dependency_overrides[get_embedding_client] = lambda: FakeEmbeddingClient(dimensions=768)
    app.dependency_overrides[get_llm_client] = lambda: llm
    with TestClient(app) as client:
        topic_id = client.post("/api/v1/topics", json={"name": "Atlas"}).json()["id"]
        for path in sorted(ATLAS_DIR.iterdir()):
            files = {"file": (path.name, path.read_bytes())}
            assert (
                client.post(f"/api/v1/topics/{topic_id}/meetings", files=files).status_code == 201
            )
        yield client, llm, topic_id


def test_board_flow_when_refreshed_merges_meetings_with_exact_quotes(setup) -> None:  # type: ignore[no-untyped-def]
    client, llm, topic_id = setup
    assert client.get(f"/api/v1/topics/{topic_id}/board").status_code == 404

    board = client.post(f"/api/v1/topics/{topic_id}/board/refresh").json()

    database = next(d for d in board["decisions"] if d["subject"] == "database choice")
    assert database["current"]["summary"] == "Switch to MongoDB."
    assert database["history"][0]["summary"] == "PostgreSQL is the main database."
    assert database["current"]["quotes"][0]["speaker"] == "Maya Chen"
    assert "MongoDB" in database["current"]["quotes"][0]["text"]
    assert board["dropped_ungrounded"] == 2  # invented line 500 and the one-line stance

    ingestion = next(a for a in board["action_items"] if a["subject"] == "ingestion api")
    assert ingestion["owner"] == "Hussnain Razaq"
    assert ingestion["due"] == "Friday, October 9"
    runbook = next(a for a in board["action_items"] if a["subject"] == "on-call runbook")
    assert runbook["owner"] is None

    assert [o["subject"] for o in board["open_items"]] == ["data retention"]
    assert board["open_items"][0]["raised_on"] == "2026-09-28"
    assert board["stances"][0]["label"] == "inferred"
    assert len(board["stances"]) == 1
    assert board["timeline"][0]["meeting_title"] == "Data model review"

    mine = client.get(
        f"/api/v1/topics/{topic_id}/board/my-action-items", params={"name": "hussnain"}
    )
    assert [a["subject"] for a in mine.json()] == ["ingestion api"]
    assert client.get(f"/api/v1/topics/{topic_id}/board").json()["topic_id"] == topic_id
    assert len(llm.calls) == 7


def test_board_flow_when_refreshed_twice_reuses_cached_extractions(setup) -> None:  # type: ignore[no-untyped-def]
    client, llm, topic_id = setup
    client.post(f"/api/v1/topics/{topic_id}/board/refresh")
    llm.replies = [stance_reply(), timeline_reply()]
    client.post(f"/api/v1/topics/{topic_id}/board/refresh")
    assert len(llm.calls) == 9  # 5 extractions once + stance and timeline twice


def test_board_flow_when_llm_down_returns_503_and_app_keeps_running(setup) -> None:  # type: ignore[no-untyped-def]
    client, llm, topic_id = setup
    llm.fail = True
    response = client.post(f"/api/v1/topics/{topic_id}/board/refresh")
    assert response.status_code == 503
    assert "not available" in response.json()["message"]
    assert client.get("/api/v1/health").status_code == 200


def test_board_flow_when_stance_fails_keeps_extractions_for_next_try(setup) -> None:  # type: ignore[no-untyped-def]
    client, llm, topic_id = setup
    llm.replies = (
        extractor_replies()
    )  # stance gets an empty queue -> {} is fine, so force a failure
    original = llm.complete_json
    count = {"n": 0}

    async def fail_after_extractions(system: str, user: str):  # type: ignore[no-untyped-def]
        count["n"] += 1
        if count["n"] == 6:
            from app.core.exceptions import ProviderError

            raise ProviderError("The language model is busy (rate limit).")
        return await original(system, user)

    llm.complete_json = fail_after_extractions  # type: ignore[method-assign]
    assert client.post(f"/api/v1/topics/{topic_id}/board/refresh").status_code == 503

    llm.complete_json = original  # type: ignore[method-assign]
    llm.calls.clear()
    llm.replies = [stance_reply(), timeline_reply()]
    assert client.post(f"/api/v1/topics/{topic_id}/board/refresh").status_code == 200
    assert len(llm.calls) == 2  # no extraction was repeated


def test_board_flow_when_rebuild_ignores_cache(setup) -> None:  # type: ignore[no-untyped-def]
    client, llm, topic_id = setup
    client.post(f"/api/v1/topics/{topic_id}/board/refresh")
    llm.calls.clear()
    llm.replies = [*extractor_replies(), stance_reply(), timeline_reply()]
    response = client.post(f"/api/v1/topics/{topic_id}/board/refresh", params={"rebuild": "true"})
    assert response.status_code == 200
    assert len(llm.calls) == 7  # all five meetings were read again


def test_board_flow_when_stance_quotes_other_speakers_drops_them(setup) -> None:  # type: ignore[no-untyped-def]
    client, llm, topic_id = setup
    reply = stance_reply()
    # Meeting 2 line 11 is spoken by Maya, not Priya: it must not be used as Priya's proof.
    reply["stances"][0]["evidence"].append({"meeting_id": 2, "line": 11})
    llm.replies = [*extractor_replies(), reply, timeline_reply()]
    board = client.post(f"/api/v1/topics/{topic_id}/board/refresh").json()
    assert {q["speaker"] for q in board["stances"][0]["quotes"]} == {"Priya Nair"}
