"""One event from live speech-to-text, forwarded to the browser as JSON."""

from typing import Literal

from pydantic import BaseModel

SpeechEventType = Literal["partial", "final", "speech_started", "utterance_end"]


class SpeechEvent(BaseModel):
    type: SpeechEventType
    text: str = ""
    speech_final: bool = False  # True when the speaker paused after this final text
