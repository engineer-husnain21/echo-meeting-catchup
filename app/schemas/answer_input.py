"""Input for the Answer agent: the question plus the context it may answer from."""

from pydantic import BaseModel


class AnswerInput(BaseModel):
    question: str
    user_name: str | None
    meetings: str  # "M3 | 2026-10-05 | Data model review", oldest first
    board_facts: str  # decisions, action items, open items and stances with [M3 L7] tags
    excerpts: str  # retrieved transcript lines as "[M3 L7 01:02] Speaker: text"
    conversation: str  # earlier turns, "User: ..." / "ECHO: ..."
