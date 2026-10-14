"""Interface for any live speech-to-text provider."""

from collections.abc import AsyncIterator
from typing import Protocol

from app.schemas.speech_event import SpeechEvent


class SpeechToTextClient(Protocol):
    """Streams audio chunks to the provider and yields transcript events as they arrive."""

    def stream(self, audio: AsyncIterator[bytes]) -> AsyncIterator[SpeechEvent]: ...
