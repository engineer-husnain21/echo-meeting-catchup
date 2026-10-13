"""One spoken line of a meeting transcript."""

from pydantic import BaseModel, Field


class TranscriptLine(BaseModel):
    """A single speaker turn with its position in the transcript."""

    line_number: int = Field(ge=1, description="1-based position in the transcript")
    speaker: str
    start_seconds: float | None = Field(default=None, ge=0)
    end_seconds: float | None = Field(default=None, ge=0)
    text: str
