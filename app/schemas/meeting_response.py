"""Meeting as returned by the API."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class MeetingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    topic_id: int
    title: str
    meeting_date: date
    source_filename: str
    file_format: str
    line_count: int
    duration_seconds: float
    uploaded_at: datetime
