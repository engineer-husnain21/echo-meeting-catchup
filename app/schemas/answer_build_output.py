"""Result of the answer orchestrator: the agent answer and every line it was shown."""

from pydantic import BaseModel, Field

from app.schemas.answer_output import AnswerOutput
from app.schemas.line_ref import LineRef


class AnswerBuildOutput(BaseModel):
    output: AnswerOutput
    shown_lines: list[LineRef] = Field(default_factory=list)  # citations must be one of these
