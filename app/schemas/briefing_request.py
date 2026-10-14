"""Request for a spoken catch-up briefing of a topic."""

from pydantic import BaseModel, Field


class BriefingRequest(BaseModel):
    user_name: str | None = Field(default=None, max_length=120)
