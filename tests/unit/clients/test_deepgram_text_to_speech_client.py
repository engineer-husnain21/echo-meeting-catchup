import json

import httpx
import pytest

from app.clients.deepgram_text_to_speech_client import DeepgramTextToSpeechClient
from app.core.exceptions import ProviderError


def _client(handler, api_key: str = "secret") -> DeepgramTextToSpeechClient:  # type: ignore[no-untyped-def]
    return DeepgramTextToSpeechClient(
        speak_url="https://deepgram.test/v1/speak",
        api_key=api_key,
        model="aura-2-thalia-en",
        transport=httpx.MockTransport(handler),
    )


async def test_synthesize_when_ok_returns_mp3_bytes() -> None:
    sent: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(request)
        return httpx.Response(200, content=b"ID3audio")

    audio = await _client(handler).synthesize("Hello there.")
    assert audio == b"ID3audio"
    assert sent[0].headers["Authorization"] == "Token secret"
    assert sent[0].url.params["model"] == "aura-2-thalia-en"
    assert sent[0].url.params["encoding"] == "mp3"
    assert json.loads(sent[0].content) == {"text": "Hello there."}


@pytest.mark.parametrize(("status", "message"), [(401, "rejected"), (500, "not available")])
async def test_synthesize_when_http_error_raises_provider_error(status: int, message: str) -> None:
    client = _client(lambda _: httpx.Response(status, text="nope"))
    with pytest.raises(ProviderError, match=message):
        await client.synthesize("Hi")


async def test_synthesize_when_network_fails_raises_provider_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down", request=request)

    with pytest.raises(ProviderError, match="not available"):
        await _client(handler).synthesize("Hi")


async def test_synthesize_when_key_missing_raises_provider_error() -> None:
    with pytest.raises(ProviderError, match="DEEPGRAM_API_KEY"):
        await _client(lambda _: httpx.Response(200), api_key="").synthesize("Hi")
