"""Result of a briefing run: the narrator output and every board line it was shown."""

from pydantic import BaseModel, Field

from app.schemas.line_ref import LineRef
from app.schemas.narrator_output import NarratorOutput


class BriefingBuildOutput(BaseModel):
    output: NarratorOutput
    shown_lines: list[LineRef] = Field(default_factory=list)
