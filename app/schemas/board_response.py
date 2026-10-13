"""The catch-up board of a topic. Every item carries exact quotes from the transcripts."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class Quote(BaseModel):
    meeting_id: int
    meeting_title: str
    meeting_date: date
    line: int
    speaker: str
    start_seconds: float | None
    text: str


class DecisionVersion(BaseModel):
    summary: str
    decided_by: str | None
    reason: str | None
    meeting_id: int
    meeting_date: date
    quotes: list[Quote]


class BoardDecision(BaseModel):
    subject: str
    current: DecisionVersion
    history: list[DecisionVersion] = Field(default_factory=list)  # older versions, oldest first


class BoardActionItem(BaseModel):
    subject: str
    task: str
    owner: str | None  # None is shown as "Unassigned"
    due: str | None
    status: Literal["open", "done"]
    meeting_id: int
    meeting_date: date
    quotes: list[Quote]


class BoardOpenItem(BaseModel):
    subject: str
    question: str
    raised_in_meeting_id: int
    raised_on: date
    quotes: list[Quote]


class BoardStance(BaseModel):
    label: Literal["inferred"] = "inferred"
    person: str
    subject: str
    leaning: str
    trend: str
    explanation: str
    quotes: list[Quote]


class BoardTimelineEntry(BaseModel):
    meeting_id: int
    meeting_title: str
    meeting_date: date
    subject: str
    change: str
    reason: str | None
    quotes: list[Quote]


class BoardMeeting(BaseModel):
    id: int
    title: str
    meeting_date: date


class BoardResponse(BaseModel):
    topic_id: int
    updated_at: datetime
    meetings: list[BoardMeeting]
    decisions: list[BoardDecision] = Field(default_factory=list)
    action_items: list[BoardActionItem] = Field(default_factory=list)
    open_items: list[BoardOpenItem] = Field(default_factory=list)
    stances: list[BoardStance] = Field(default_factory=list)
    timeline: list[BoardTimelineEntry] = Field(default_factory=list)
    dropped_ungrounded: int = 0  # items removed because their cited lines did not exist
