"""Text-to-speech with Deepgram Aura-2 (REST). Returns MP3 bytes."""

import httpx

from app.core.exceptions import ProviderError
from app.core.logging import get_logger

_logger = get_logger("speech")


class DeepgramTextToSpeechClient:
    def __init__(
        self,
        speak_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float = 20.0,
        transport: httpx.AsyncBaseTransport | None = None,  # tests pass a mock transport
    ) -> None:
        self._speak_url = speak_url
        self._api_key = api_key
        self._model = model
        self._timeout_seconds = timeout_seconds
        self._transport = transport

    async def synthesize(self, text: str) -> bytes:
        if not self._api_key:
            raise ProviderError("Text-to-speech is not set up (DEEPGRAM_API_KEY is empty).")
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout_seconds, transport=self._transport
            ) as client:
                response = await client.post(
                    self._speak_url,
                    params={"model": self._model, "encoding": "mp3"},
                    headers={"Authorization": f"Token {self._api_key}"},
                    json={"text": text},
                )
        except httpx.HTTPError as error:
            _logger.warning("Deepgram TTS request failed: %r", error)
            raise ProviderError("The speech service is not available right now.") from error
        if response.status_code in (401, 403):
            raise ProviderError("Deepgram rejected the API key.")
        if response.status_code >= 400:
            _logger.warning("Deepgram TTS HTTP %s: %s", response.status_code, response.text[:300])
            raise ProviderError("The speech service is not available right now.")
        _logger.info("Synthesized %d characters into %d bytes", len(text), len(response.content))
        return response.content
