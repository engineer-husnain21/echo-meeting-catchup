"""A group of consecutive transcript lines that is embedded and searched as one unit."""

from datetime import date

from pydantic import BaseModel


class TranscriptChunk(BaseModel):
    topic_id: int
    meeting_id: int
    meeting_title: str
    meeting_date: date
    chunk_index: int
    first_line: int
    last_line: int
    start_seconds: float | None
    speakers: list[str]
    text: str
