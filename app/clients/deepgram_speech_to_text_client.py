"""Live speech-to-text with Deepgram (Nova-3) over a WebSocket.

The browser never sees the API key: it streams audio to our backend, and this client
forwards it to Deepgram and turns Deepgram's JSON messages into SpeechEvent objects.
"""

import asyncio
import json
from collections.abc import AsyncIterator
from contextlib import suppress
from typing import Any
from urllib.parse import urlencode

from websockets.asyncio.client import ClientConnection, connect
from websockets.exceptions import ConnectionClosed, InvalidStatus, WebSocketException

from app.core.exceptions import ProviderError
from app.core.logging import get_logger
from app.schemas.speech_event import SpeechEvent

_logger = get_logger("speech")
_KEEP_ALIVE = json.dumps({"type": "KeepAlive"})
_CLOSE_STREAM = json.dumps({"type": "CloseStream"})


class DeepgramSpeechToTextClient:
    def __init__(
        self,
        listen_url: str,
        api_key: str,
        model: str,
        endpointing_ms: int,
        utterance_end_ms: int,
        keep_alive_seconds: float = 4.0,
        open_timeout_seconds: float = 10.0,
    ) -> None:
        self._listen_url = listen_url
        self._api_key = api_key
        self._model = model
        self._endpointing_ms = endpointing_ms
        self._utterance_end_ms = utterance_end_ms
        self._keep_alive_seconds = keep_alive_seconds
        self._open_timeout_seconds = open_timeout_seconds

    async def stream(self, audio: AsyncIterator[bytes]) -> AsyncIterator[SpeechEvent]:
        if not self._api_key:
            raise ProviderError("Speech-to-text is not set up (DEEPGRAM_API_KEY is empty).")
        try:
            async with connect(
                self._url(),
                additional_headers={"Authorization": f"Token {self._api_key}"},
                open_timeout=self._open_timeout_seconds,
            ) as connection:
                _logger.info("Deepgram live stream opened")
                sender = asyncio.create_task(self._send_audio(connection, audio))
                keeper = asyncio.create_task(self._keep_alive(connection))
                try:
                    async for message in connection:
                        if isinstance(message, str):
                            event = parse_message(message)
                            if event:
                                yield event
                finally:
                    for task in (sender, keeper):
                        task.cancel()
                    for task in (sender, keeper):
                        with suppress(asyncio.CancelledError, ConnectionClosed):
                            await task
                _logger.info("Deepgram live stream closed")
        except InvalidStatus as error:
            code = error.response.status_code
            _logger.warning("Deepgram refused the stream: HTTP %s", code)
            reason = (
                "Deepgram rejected the API key."
                if code in (401, 403)
                else "The speech service is not available right now."
            )
            raise ProviderError(reason) from error
        except (OSError, TimeoutError, WebSocketException) as error:
            _logger.warning("Deepgram stream failed: %r", error)
            raise ProviderError("The speech service is not available right now.") from error

    def _url(self) -> str:
        params = {
            "model": self._model,
            "language": "en",
            "smart_format": "true",
            "interim_results": "true",
            "endpointing": str(self._endpointing_ms),
            "utterance_end_ms": str(self._utterance_end_ms),
            "vad_events": "true",
        }
        return f"{self._listen_url}?{urlencode(params)}"

    @staticmethod
    async def _send_audio(connection: ClientConnection, audio: AsyncIterator[bytes]) -> None:
        """Forward audio until the browser stops, then ask Deepgram to flush and close."""
        try:
            async for chunk in audio:
                if chunk:
                    await connection.send(chunk)
            await connection.send(_CLOSE_STREAM)
        except ConnectionClosed:
            pass

    async def _keep_alive(self, connection: ClientConnection) -> None:
        """Deepgram closes idle streams after ~10 s, for example while ECHO is speaking."""
        while True:
            await asyncio.sleep(self._keep_alive_seconds)
            await connection.send(_KEEP_ALIVE)


def parse_message(raw: str) -> SpeechEvent | None:
    """Turn one Deepgram JSON message into an event, or None if it is not useful."""
    try:
        data: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError:
        return None
    kind = data.get("type")
    if kind == "SpeechStarted":
        return SpeechEvent(type="speech_started")
    if kind == "UtteranceEnd":
        return SpeechEvent(type="utterance_end")
    if kind != "Results":
        if kind == "Error":
            _logger.warning("Deepgram error message: %s", raw[:300])
        return None
    alternatives = (data.get("channel") or {}).get("alternatives") or [{}]
    text = str(alternatives[0].get("transcript") or "").strip()
    if not text:
        return None
    if data.get("is_final"):
        return SpeechEvent(type="final", text=text, speech_final=bool(data.get("speech_final")))
    return SpeechEvent(type="partial", text=text)
