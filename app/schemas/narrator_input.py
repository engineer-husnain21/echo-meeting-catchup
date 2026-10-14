"""Input for the Narrator agent: the board as tagged facts, and who is listening."""

from pydantic import BaseModel


class NarratorInput(BaseModel):
    user_name: str | None
    meetings: str  # "M3 | 2026-10-05 | Data model review", oldest first
    board_facts: str  # decisions, action items, open items and stances with [M3 L7] tags
