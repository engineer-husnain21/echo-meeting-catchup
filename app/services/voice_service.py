"""Voice features: live transcription of the user's speech and spoken answers."""

import re
from collections.abc import AsyncIterator

from app.clients.speech_to_text_client import SpeechToTextClient
from app.clients.text_to_speech_client import TextToSpeechClient
from app.core.exceptions import ValidationError
from app.schemas.speech_event import SpeechEvent

_SENTENCE_END = re.compile(r"(?<=[.!?])\s")


class VoiceService:
    def __init__(
        self, stt: SpeechToTextClient, tts: TextToSpeechClient, max_speech_chars: int
    ) -> None:
        self._stt = stt
        self._tts = tts
        self._max_speech_chars = max_speech_chars

    def transcribe(self, audio: AsyncIterator[bytes]) -> AsyncIterator[SpeechEvent]:
        """Pass the audio stream to the speech-to-text provider and yield its events."""
        return self._stt.stream(audio)

    async def speak(self, text: str) -> bytes:
        cleaned = " ".join(text.split())
        if not cleaned:
            raise ValidationError("There is no text to speak.")
        return await self._tts.synthesize(self._shorten(cleaned))

    def _shorten(self, text: str) -> str:
        """Long answers are cut at the last full sentence that fits, to keep TTS fast."""
        if len(text) <= self._max_speech_chars:
            return text
        head = text[: self._max_speech_chars]
        ends = [m.start() for m in _SENTENCE_END.finditer(head)]
        return head[: ends[-1]] if ends else head
