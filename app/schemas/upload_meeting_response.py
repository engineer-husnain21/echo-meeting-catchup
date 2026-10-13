"""Result of uploading one transcript."""

from pydantic import BaseModel

from app.schemas.meeting_response import MeetingResponse


class UploadMeetingResponse(BaseModel):
    meeting: MeetingResponse
    chunk_count: int
    speakers: list[str]
