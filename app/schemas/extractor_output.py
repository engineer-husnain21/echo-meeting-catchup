"""Output of the Extractor agent. Line numbers point into the meeting that was given."""

from typing import Literal

from pydantic import BaseModel, Field


class ExtractedDecision(BaseModel):
    subject: str
    summary: str
    decided_by: str | None = None
    reason: str | None = None
    lines: list[int] = Field(default_factory=list)


class ExtractedActionItem(BaseModel):
    subject: str
    task: str
    owner: str | None = None  # None means nobody took it ("Unassigned")
    due: str | None = None
    status: Literal["open", "done"] = "open"
    lines: list[int] = Field(default_factory=list)


class ExtractedOpenItem(BaseModel):
    subject: str
    question: str
    lines: list[int] = Field(default_factory=list)


class ExtractorOutput(BaseModel):
    decisions: list[ExtractedDecision] = Field(default_factory=list)
    action_items: list[ExtractedActionItem] = Field(default_factory=list)
    open_items: list[ExtractedOpenItem] = Field(default_factory=list)
