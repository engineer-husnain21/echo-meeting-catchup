"""Fake speech clients: no network, record what they received."""

from collections.abc import AsyncIterator

from app.core.exceptions import ProviderError
from app.schemas.speech_event import SpeechEvent


class FakeSpeechToTextClient:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.received: list[bytes] = []

    async def stream(self, audio: AsyncIterator[bytes]) -> AsyncIterator[SpeechEvent]:
        if self.fail:
            raise ProviderError("The speech service is not available right now.")
        yield SpeechEvent(type="speech_started")
        async for chunk in audio:
            self.received.append(chunk)
            yield SpeechEvent(type="partial", text=f"heard {len(self.received)}")
        yield SpeechEvent(type="final", text="Which database are we using?", speech_final=True)
        yield SpeechEvent(type="utterance_end")


class FakeTextToSpeechClient:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.texts: list[str] = []

    async def synthesize(self, text: str) -> bytes:
        self.texts.append(text)
        if self.fail:
            raise ProviderError("The speech service is not available right now.")
        return b"ID3fake-mp3"
