from app.parsers.txt_transcript_parser import TxtTranscriptParser
from tests.sample_data import ATLAS_DIR


def test_parse_when_sample_meeting_reads_all_turns() -> None:
    content = (ATLAS_DIR / "2026-09-30_architecture-review.txt").read_bytes()
    lines = TxtTranscriptParser().parse(content)
    assert len(lines) == 25
    assert lines[1].speaker == "Daniel Brooks"
    assert lines[1].start_seconds is not None


def test_parse_when_header_layout_joins_text_lines() -> None:
    content = b"Priya Nair   0:15\nThe queue is stable.\n\nMaya Chen 0:20\nGood.\n"
    lines = TxtTranscriptParser().parse(content)
    assert [(line.speaker, line.start_seconds, line.text) for line in lines] == [
        ("Priya Nair", 15.0, "The queue is stable."),
        ("Maya Chen", 20.0, "Good."),
    ]


def test_parse_when_continuation_rows_appends_to_last_turn() -> None:
    content = b"[00:00:01] Maya Chen: First part\nsecond part\n"
    assert TxtTranscriptParser().parse(content)[0].text == "First part second part"


def test_parse_when_no_timestamps_reads_plain_speaker_lines() -> None:
    lines = TxtTranscriptParser().parse(b"Maya Chen: Hello.\nOmar Haddad: Hi.\n")
    assert [line.speaker for line in lines] == ["Maya Chen", "Omar Haddad"]
    assert lines[0].start_seconds is None
