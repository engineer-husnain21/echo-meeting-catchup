"""A 3+ hour meeting (generated in memory, so the repo stays small) must upload and build."""

from fastapi.testclient import TestClient

from app.core.dependencies import get_embedding_client, get_llm_client
from app.main import create_app
from tests.fakes.fake_embedding_client import FakeEmbeddingClient
from tests.fakes.fake_llm_client import FakeLlmClient

SPEAKERS = ["Maya Chen", "Daniel Brooks", "Priya Nair", "Omar Haddad"]
LINES = 2200  # one line every 5 seconds is just over 3 hours


def _stamp(seconds: int) -> str:
    return f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}.000"


def _long_vtt() -> bytes:
    cues = ["WEBVTT", ""]
    for n in range(LINES):
        start, end = n * 5, n * 5 + 4
        speaker = SPEAKERS[n % len(SPEAKERS)]
        cues += [f"{_stamp(start)} --> {_stamp(end)}", f"<v {speaker}>Point {n} on rollout.", ""]
    return "\n".join(cues).encode()


def test_long_meeting_flow_when_three_hours_uploads_and_reads_in_windows() -> None:
    llm = FakeLlmClient()
    app = create_app()
    app.dependency_overrides[get_embedding_client] = lambda: FakeEmbeddingClient(dimensions=768)
    app.dependency_overrides[get_llm_client] = lambda: llm
    with TestClient(app) as client:
        topic_id = client.post("/api/v1/topics", json={"name": "Long"}).json()["id"]
        files = {"file": ("2026-10-13_quarterly-planning.vtt", _long_vtt())}
        upload = client.post(f"/api/v1/topics/{topic_id}/meetings", files=files)
        assert upload.status_code == 201
        assert upload.json()["meeting"]["line_count"] == LINES
        assert upload.json()["meeting"]["duration_seconds"] > 3 * 3600

        board = client.post(f"/api/v1/topics/{topic_id}/board/refresh")
        assert board.status_code == 200

    windows = -(-LINES // 150)  # EXTRACT_WINDOW_LINES default
    extractor_calls = [c for c in llm.calls if "Extractor agent" in c[0]]
    assert len(extractor_calls) == windows  # 15 calls, each under the token limit
    stance_prompt = next(c[1] for c in llm.calls if "Stance agent" in c[0])
    assert stance_prompt.count("Point ") <= 400  # STANCE_MAX_LINES sampling
