from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.core.dependencies import get_speech_to_text_client, get_text_to_speech_client
from app.main import create_app
from tests.fakes.fake_speech_clients import FakeSpeechToTextClient, FakeTextToSpeechClient


@pytest.fixture
def voice() -> Iterator[tuple[TestClient, FakeSpeechToTextClient, FakeTextToSpeechClient]]:
    stt, tts = FakeSpeechToTextClient(), FakeTextToSpeechClient()
    app = create_app()
    app.dependency_overrides[get_speech_to_text_client] = lambda: stt
    app.dependency_overrides[get_text_to_speech_client] = lambda: tts
    with TestClient(app) as client:
        yield client, stt, tts


def test_voice_flow_when_audio_streamed_then_stop_returns_events_and_closed(voice) -> None:  # type: ignore[no-untyped-def]
    client, stt, _ = voice
    with client.websocket_connect("/api/v1/voice/transcribe") as ws:
        assert ws.receive_json()["type"] == "speech_started"
        ws.send_bytes(b"chunk-1")
        assert ws.receive_json() == {"type": "partial", "text": "heard 1", "speech_final": False}
        ws.send_bytes(b"chunk-2")
        ws.receive_json()
        ws.send_json({"type": "stop"})
        final = ws.receive_json()
        assert final["type"] == "final" and final["speech_final"] is True
        assert ws.receive_json()["type"] == "utterance_end"
        assert ws.receive_json() == {"type": "closed"}
    assert stt.received == [b"chunk-1", b"chunk-2"]


def test_voice_flow_when_speech_service_down_sends_error_event(voice) -> None:  # type: ignore[no-untyped-def]
    client, stt, _ = voice
    stt.fail = True
    with client.websocket_connect("/api/v1/voice/transcribe") as ws:
        event = ws.receive_json()
    assert event == {"type": "error", "message": "The speech service is not available right now."}
    assert client.get("/api/v1/health").status_code == 200


def test_voice_flow_when_text_posted_returns_mp3(voice) -> None:  # type: ignore[no-untyped-def]
    client, _, tts = voice
    response = client.post("/api/v1/voice/speech", json={"text": "We are using MongoDB."})
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
    assert response.content.startswith(b"ID3")
    assert tts.texts == ["We are using MongoDB."]


def test_voice_flow_when_tts_down_returns_503(voice) -> None:  # type: ignore[no-untyped-def]
    client, _, tts = voice
    tts.fail = True
    response = client.post("/api/v1/voice/speech", json={"text": "Hi"})
    assert response.status_code == 503
