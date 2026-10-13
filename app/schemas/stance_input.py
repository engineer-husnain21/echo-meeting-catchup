"""Input for the Stance agent: all meetings of a topic."""

from pydantic import BaseModel


class StanceInput(BaseModel):
    speakers: list[str]
    meetings: str  # meeting headers + lines formatted as "[M3 L12 05:31] Speaker: text"
    known_subjects: list[str]
