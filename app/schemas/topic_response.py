"""Topic as returned by the API."""

from datetime import datetime

from pydantic import BaseModel


class TopicResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    meeting_count: int
