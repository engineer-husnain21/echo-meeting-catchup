from collections.abc import AsyncIterator

import pytest

from app.core.exceptions import ValidationError
from app.services.voice_service import VoiceService
from tests.fakes.fake_speech_clients import FakeSpeechToTextClient, FakeTextToSpeechClient


async def _audio() -> AsyncIterator[bytes]:
    yield b"one"
    yield b"two"


async def test_transcribe_when_audio_streams_yields_provider_events() -> None:
    stt = FakeSpeechToTextClient()
    service = VoiceService(stt, FakeTextToSpeechClient(), max_speech_chars=100)
    events = [e async for e in service.transcribe(_audio())]
    assert events[-2].text == "Which database are we using?"
    assert stt.received == [b"one", b"two"]


async def test_speak_when_text_long_cuts_at_last_full_sentence() -> None:
    tts = FakeTextToSpeechClient()
    service = VoiceService(FakeSpeechToTextClient(), tts, max_speech_chars=30)
    audio = await service.speak("First sentence here.   Second one is longer than the limit.")
    assert audio.startswith(b"ID3")
    assert tts.texts == ["First sentence here."]


async def test_speak_when_text_blank_raises_validation_error() -> None:
    service = VoiceService(FakeSpeechToTextClient(), FakeTextToSpeechClient(), 100)
    with pytest.raises(ValidationError):
        await service.speak("  \n ")
