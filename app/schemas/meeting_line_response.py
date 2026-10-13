"""One transcript line for the transcript viewer."""

from pydantic import BaseModel, ConfigDict


class MeetingLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    line_number: int
    speaker: str
    start_seconds: float | None
    end_seconds: float | None
    text: str
