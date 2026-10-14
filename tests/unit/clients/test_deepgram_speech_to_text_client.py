import json
from collections.abc import AsyncIterator
from http import HTTPStatus

import pytest
from websockets.asyncio.server import Request, Response, ServerConnection, serve

from app.clients.deepgram_speech_to_text_client import DeepgramSpeechToTextClient, parse_message
from app.core.exceptions import ProviderError
from app.schemas.speech_event import SpeechEvent


def _results(text: str, is_final: bool, speech_final: bool = False) -> str:
    return json.dumps(
        {
            "type": "Results",
            "is_final": is_final,
            "speech_final": speech_final,
            "channel": {"alternatives": [{"transcript": text}]},
        }
    )


def test_parse_message_when_results_returns_partial_or_final() -> None:
    assert parse_message(_results("which data", False)) == SpeechEvent(
        type="partial", text="which data"
    )
    final = parse_message(_results("Which database?", True, speech_final=True))
    assert final == SpeechEvent(type="final", text="Which database?", speech_final=True)


def test_parse_message_when_other_messages_maps_or_skips_them() -> None:
    assert parse_message('{"type": "SpeechStarted"}') == SpeechEvent(type="speech_started")
    assert parse_message('{"type": "UtteranceEnd"}') == SpeechEvent(type="utterance_end")
    assert parse_message(_results("", True)) is None  # silence
    assert parse_message('{"type": "Metadata"}') is None
    assert parse_message("not json") is None


async def _audio(*chunks: bytes) -> AsyncIterator[bytes]:
    for chunk in chunks:
        yield chunk


def _client(port: int, api_key: str = "secret") -> DeepgramSpeechToTextClient:
    return DeepgramSpeechToTextClient(
        listen_url=f"ws://127.0.0.1:{port}/v1/listen",
        api_key=api_key,
        model="nova-3",
        endpointing_ms=300,
        utterance_end_ms=1000,
        keep_alive_seconds=0.05,
        open_timeout_seconds=2,
    )


async def test_stream_when_deepgram_answers_forwards_audio_and_yields_events() -> None:
    seen: dict[str, object] = {"audio": [], "text": []}

    async def fake_deepgram(connection: ServerConnection) -> None:
        seen["auth"] = connection.request.headers["Authorization"]  # type: ignore[union-attr]
        seen["path"] = connection.request.path  # type: ignore[union-attr]
        await connection.send('{"type": "SpeechStarted"}')
        async for message in connection:
            if isinstance(message, bytes):
                seen["audio"].append(message)  # type: ignore[union-attr]
                continue
            seen["text"].append(json.loads(message)["type"])  # type: ignore[union-attr]
            if json.loads(message)["type"] == "CloseStream":
                await connection.send(_results("Which database?", True, True))
                await connection.send('{"type": "UtteranceEnd"}')
                await connection.close()

    async with serve(fake_deepgram, "127.0.0.1", 0) as server:
        port = server.sockets[0].getsockname()[1]
        events = [e async for e in _client(port).stream(_audio(b"a1", b"", b"a2"))]

    assert [e.type for e in events] == ["speech_started", "final", "utterance_end"]
    assert events[1].text == "Which database?"
    assert seen["auth"] == "Token secret"
    assert "model=nova-3" in str(seen["path"]) and "interim_results=true" in str(seen["path"])
    assert seen["audio"] == [b"a1", b"a2"]  # empty chunk skipped
    assert seen["text"][-1] == "CloseStream"  # type: ignore[index]


async def test_stream_when_idle_sends_keep_alive() -> None:
    kinds: list[str] = []

    async def fake_deepgram(connection: ServerConnection) -> None:
        async for message in connection:
            if isinstance(message, str):
                kinds.append(json.loads(message)["type"])
                if kinds.count("KeepAlive") >= 2:
                    await connection.close()

    async def slow_audio() -> AsyncIterator[bytes]:
        import asyncio

        await asyncio.sleep(1)
        yield b"late"

    async with serve(fake_deepgram, "127.0.0.1", 0) as server:
        port = server.sockets[0].getsockname()[1]
        assert [e async for e in _client(port).stream(slow_audio())] == []
    assert kinds.count("KeepAlive") >= 2


async def test_stream_when_key_rejected_raises_provider_error() -> None:
    def reject(connection: ServerConnection, request: Request) -> Response:
        return connection.respond(HTTPStatus.UNAUTHORIZED, "bad key\n")

    async def never(connection: ServerConnection) -> None:  # pragma: no cover
        await connection.close()

    async with serve(never, "127.0.0.1", 0, process_request=reject) as server:
        port = server.sockets[0].getsockname()[1]
        with pytest.raises(ProviderError, match="rejected the API key"):
            [e async for e in _client(port).stream(_audio(b"a"))]


async def test_stream_when_server_unreachable_raises_provider_error() -> None:
    with pytest.raises(ProviderError, match="not available"):
        [e async for e in _client(9).stream(_audio(b"a"))]


async def test_stream_when_key_missing_raises_provider_error() -> None:
    with pytest.raises(ProviderError, match="DEEPGRAM_API_KEY"):
        [e async for e in _client(9, api_key="").stream(_audio(b"a"))]
