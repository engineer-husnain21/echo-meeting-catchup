"""Input for the Timeline agent: meetings in order plus every recorded decision."""

from pydantic import BaseModel


class TimelineInput(BaseModel):
    meetings: str  # one line per meeting: "M3 | 2026-10-05 | Data model review"
    decisions: str  # one line per decision with subject, meeting, summary, reason and line refs
