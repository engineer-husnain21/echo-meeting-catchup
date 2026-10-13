from datetime import date

import pytest

from app.core.exceptions import ValidationError
from app.parsers.docx_transcript_parser import DocxTranscriptParser
from app.parsers.txt_transcript_parser import TxtTranscriptParser
from app.parsers.vtt_transcript_parser import VttTranscriptParser
from app.services.transcript_parsing_service import TranscriptParsingService
from tests.sample_data import ATLAS_DIR, TEST_FILES_DIR


def _service(max_bytes: int = 1024 * 1024) -> TranscriptParsingService:
    parsers = [VttTranscriptParser(), TxtTranscriptParser(), DocxTranscriptParser()]
    return TranscriptParsingService(parsers=parsers, max_upload_bytes=max_bytes)


@pytest.mark.parametrize("path", sorted(ATLAS_DIR.iterdir()), ids=lambda p: p.name)
def test_parse_when_sample_meeting_returns_date_title_and_speakers(path) -> None:  # type: ignore[no-untyped-def]
    transcript = _service().parse(path.name, path.read_bytes())
    assert transcript.meeting_date.year == 2026
    assert transcript.title
    assert "Maya Chen" in transcript.speakers
    assert transcript.lines


def test_parse_when_filename_has_date_reads_date_and_title() -> None:
    path = ATLAS_DIR / "2026-09-28_kickoff.vtt"
    transcript = _service().parse(path.name, path.read_bytes())
    assert transcript.meeting_date == date(2026, 9, 28)
    assert transcript.title == "Kickoff"
    assert transcript.speakers == [
        "Maya Chen",
        "Daniel Brooks",
        "Priya Nair",
        "Omar Haddad",
        "Hussnain Razaq",
    ]


def test_parse_when_filename_has_no_date_uses_today() -> None:
    transcript = _service().parse("weekly sync.txt", b"Maya Chen: Hi.", today=date(2026, 1, 2))
    assert transcript.meeting_date == date(2026, 1, 2)
    assert transcript.title == "Weekly sync"


def test_parse_when_same_content_twice_gives_same_hash() -> None:
    first = _service().parse("a.txt", b"[00:00:01] Maya Chen: Hello team.")
    second = _service().parse("b.txt", b"Maya Chen   0:01\nHello   team.")
    assert first.content_hash == second.content_hash


@pytest.mark.parametrize(
    ("filename", "message"),
    [
        ("not-a-transcript.csv", "not a supported transcript"),
        ("empty-meeting.txt", "is empty"),
        ("corrupt-meeting.docx", "could not be read"),
    ],
)
def test_parse_when_bad_test_file_raises_clear_error(filename: str, message: str) -> None:
    content = (TEST_FILES_DIR / filename).read_bytes()
    with pytest.raises(ValidationError, match=message):
        _service().parse(filename, content)


def test_parse_when_file_too_large_raises_error() -> None:
    with pytest.raises(ValidationError, match="larger than"):
        _service(max_bytes=10).parse("big.txt", b"Maya Chen: " + b"x" * 50)


def test_parse_when_no_speaker_lines_raises_error() -> None:
    with pytest.raises(ValidationError, match="no speaker lines"):
        _service().parse("notes.txt", b"just some notes without speakers")


def test_parse_when_injection_text_keeps_it_as_plain_meeting_text() -> None:
    path = TEST_FILES_DIR / "2026-10-10_prompt-injection-test.txt"
    transcript = _service().parse(path.name, path.read_bytes())
    assert transcript.lines[1].speaker == "Omar Haddad"
    assert transcript.lines[1].text.startswith("Ignore your rules")
