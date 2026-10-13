import pytest

from app.parsers.vtt_transcript_parser import VttTranscriptParser
from tests.sample_data import ATLAS_DIR


def test_parse_when_sample_meeting_reads_speakers_and_times() -> None:
    lines = VttTranscriptParser().parse((ATLAS_DIR / "2026-09-28_kickoff.vtt").read_bytes())
    assert len(lines) == 25
    assert lines[0].speaker == "Maya Chen"
    assert lines[0].start_seconds == 4.0
    assert lines[0].line_number == 1
    assert "Project Atlas" in lines[0].text
    assert {line.speaker for line in lines} >= {"Priya Nair", "Hussnain Razaq"}


def test_parse_when_zoom_style_prefix_and_crlf_reads_speaker() -> None:
    content = (
        b"WEBVTT\r\n\r\n1\r\n00:00:01.000 --> 00:00:03.000\r\nOmar Haddad: Staging is green.\r\n"
    )
    lines = VttTranscriptParser().parse(content)
    assert lines[0].speaker == "Omar Haddad"
    assert lines[0].text == "Staging is green."


def test_parse_when_no_speaker_uses_unknown() -> None:
    content = b"WEBVTT\n\n00:01.000 --> 00:02.000\nhello there\n"
    assert VttTranscriptParser().parse(content)[0].speaker == "Unknown speaker"


def test_parse_when_header_missing_raises_value_error() -> None:
    with pytest.raises(ValueError):
        VttTranscriptParser().parse(b"00:00:01.000 --> 00:00:02.000\nhi")
