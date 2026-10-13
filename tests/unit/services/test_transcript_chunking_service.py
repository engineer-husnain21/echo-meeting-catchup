from datetime import date

import pytest

from app.models.meeting import Meeting
from app.models.meeting_line import MeetingLine
from app.services.transcript_chunking_service import TranscriptChunkingService


def _meeting() -> Meeting:
    return Meeting(id=7, topic_id=3, title="Kickoff", meeting_date=date(2026, 9, 28))


def _lines(count: int) -> list[MeetingLine]:
    return [
        MeetingLine(line_number=i, speaker=f"S{i % 2}", start_seconds=i * 61.0, text=f"t{i}")
        for i in range(1, count + 1)
    ]


def test_chunk_when_ten_lines_size_six_overlap_two_makes_two_chunks() -> None:
    chunks = TranscriptChunkingService(6, 2).chunk(_meeting(), _lines(10))
    assert [(c.first_line, c.last_line) for c in chunks] == [(1, 6), (5, 10)]
    assert chunks[0].topic_id == 3 and chunks[0].meeting_id == 7
    assert chunks[0].text.splitlines()[0] == "[L1 01:01] S1: t1"


def test_chunk_when_fewer_lines_than_size_makes_one_chunk() -> None:
    chunks = TranscriptChunkingService(6, 2).chunk(_meeting(), _lines(3))
    assert len(chunks) == 1
    assert chunks[0].speakers == ["S1", "S0"]


def test_chunk_when_long_meeting_formats_hours() -> None:
    line = MeetingLine(line_number=1, speaker="A", start_seconds=3725.0, text="x")
    chunk = TranscriptChunkingService(6, 2).chunk(_meeting(), [line])[0]
    assert chunk.text == "[L1 1:02:05] A: x"


def test_init_when_overlap_too_big_raises() -> None:
    with pytest.raises(ValueError):
        TranscriptChunkingService(4, 4)
