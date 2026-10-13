"""A full meeting transcript for the viewer."""

from pydantic import BaseModel

from app.schemas.meeting_line_response import MeetingLineResponse
from app.schemas.meeting_response import MeetingResponse


class MeetingTranscriptResponse(BaseModel):
    meeting: MeetingResponse
    lines: list[MeetingLineResponse]
