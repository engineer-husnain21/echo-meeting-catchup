"""Text that ECHO should say out loud."""

from pydantic import BaseModel, Field


class SpeakRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
