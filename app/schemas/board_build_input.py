"""What the board orchestrator needs: the meetings in date order and cached extractions."""

from datetime import date

from pydantic import BaseModel, Field

from app.schemas.extractor_output import ExtractorOutput


class MeetingText(BaseModel):
    meeting_id: int
    title: str
    meeting_date: date
    speakers: list[str]
    lines: list[str]  # "[L12 05:31] Speaker: text"


class BoardBuildInput(BaseModel):
    meetings: list[MeetingText]  # oldest first
    cached: dict[int, ExtractorOutput] = Field(default_factory=dict)
