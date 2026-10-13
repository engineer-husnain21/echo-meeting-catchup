"""Input for the Extractor agent: one meeting at a time."""

from datetime import date

from pydantic import BaseModel


class ExtractorInput(BaseModel):
    meeting_title: str
    meeting_date: date
    speakers: list[str]
    transcript: str  # lines formatted as "[L12 05:31] Speaker: text"
    known_subjects: list[str]  # subjects from earlier meetings, reused for consistent keys
