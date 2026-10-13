"""Output of the Timeline agent: what changed across meetings and why."""

from pydantic import BaseModel, Field

from app.schemas.line_ref import LineRef


class TimelineChange(BaseModel):
    meeting_id: int
    subject: str
    change: str
    reason: str | None = None
    evidence: list[LineRef] = Field(default_factory=list)


class TimelineOutput(BaseModel):
    changes: list[TimelineChange] = Field(default_factory=list)
