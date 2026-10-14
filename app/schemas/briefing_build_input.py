"""What the briefing run needs: the stored board and who is listening."""

from pydantic import BaseModel

from app.schemas.board_response import BoardMeeting, BoardResponse


class BriefingBuildInput(BaseModel):
    user_name: str | None = None
    meetings: list[BoardMeeting]  # oldest first
    board: BoardResponse
