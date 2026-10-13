import pytest

from app.parsers.docx_transcript_parser import DocxTranscriptParser
from tests.sample_data import ATLAS_DIR, TEST_FILES_DIR


def test_parse_when_sample_meeting_reads_speaker_header_layout() -> None:
    content = (ATLAS_DIR / "2026-10-05_data-model-review.docx").read_bytes()
    lines = DocxTranscriptParser().parse(content)
    assert len(lines) == 23
    assert lines[0].speaker == "Maya Chen"
    assert lines[0].start_seconds == 4.0
    assert "MongoDB" in " ".join(line.text for line in lines)


def test_parse_when_corrupt_file_raises_value_error() -> None:
    with pytest.raises(ValueError):
        DocxTranscriptParser().parse((TEST_FILES_DIR / "corrupt-meeting.docx").read_bytes())
