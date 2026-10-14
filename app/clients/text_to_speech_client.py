"""Interface for any text-to-speech provider."""

from typing import Protocol


class TextToSpeechClient(Protocol):
    """Turns text into audio bytes (MP3)."""

    async def synthesize(self, text: str) -> bytes: ...
