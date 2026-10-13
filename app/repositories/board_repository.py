"""Reads and writes cached extractions and board snapshots."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.board_snapshot import BoardSnapshot
from app.models.meeting_extraction import MeetingExtraction
from app.schemas.board_response import BoardResponse
from app.schemas.extractor_output import ExtractorOutput


class BoardRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_extractions(self, meeting_ids: list[int]) -> dict[int, ExtractorOutput]:
        if not meeting_ids:
            return {}
        result = await self._session.execute(
            select(MeetingExtraction).where(MeetingExtraction.meeting_id.in_(meeting_ids))
        )
        return {
            row.meeting_id: ExtractorOutput.model_validate_json(row.data)
            for row in result.scalars()
        }

    async def save_extraction(self, meeting_id: int, output: ExtractorOutput) -> None:
        await self._session.merge(
            MeetingExtraction(meeting_id=meeting_id, data=output.model_dump_json())
        )
        await self._session.commit()

    async def get_board(self, topic_id: int) -> BoardResponse | None:
        snapshot = await self._session.get(BoardSnapshot, topic_id)
        return BoardResponse.model_validate_json(snapshot.data) if snapshot else None

    async def save_board(self, board: BoardResponse) -> None:
        await self._session.merge(
            BoardSnapshot(
                topic_id=board.topic_id, data=board.model_dump_json(), updated_at=datetime.now(UTC)
            )
        )
        await self._session.commit()
