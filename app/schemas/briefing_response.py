"""A spoken catch-up briefing with quotes that open the source lines."""

from pydantic import BaseModel, Field

from app.schemas.board_response import Quote


class BriefingResponse(BaseModel):
    briefing: str
    citations: list[Quote] = Field(default_factory=list)
    elapsed_ms: int
