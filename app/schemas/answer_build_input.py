"""What the answer orchestrator needs: the question, recent turns and the found context."""

from pydantic import BaseModel, Field

from app.schemas.board_response import BoardMeeting, BoardResponse
from app.schemas.chat_turn import ChatTurn
from app.schemas.scored_chunk import ScoredChunk


class AnswerBuildInput(BaseModel):
    question: str
    user_name: str | None = None
    history: list[ChatTurn] = Field(default_factory=list)
    meetings: list[BoardMeeting]  # oldest first
    chunks: list[ScoredChunk] = Field(default_factory=list)
    board: BoardResponse | None = None
