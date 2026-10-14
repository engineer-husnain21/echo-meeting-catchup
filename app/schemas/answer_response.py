"""ECHO's answer to a question, with exact quotes that open the source lines."""

from pydantic import BaseModel, Field

from app.schemas.answer_output import AnswerStatus
from app.schemas.board_response import Quote


class AnswerResponse(BaseModel):
    status: AnswerStatus  # "clarify" means the answer is a question back to the user
    answer: str
    citations: list[Quote] = Field(default_factory=list)
    elapsed_ms: int
