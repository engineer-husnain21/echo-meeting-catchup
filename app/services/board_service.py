"""Builds, stores and serves the catch-up board of a topic."""

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.models.meeting_line import MeetingLine
from app.orchestrators.board_orchestrator import BoardOrchestrator
from app.repositories.board_repository import BoardRepository
from app.repositories.meeting_repository import MeetingRepository
from app.repositories.topic_repository import TopicRepository
from app.schemas.board_build_input import BoardBuildInput, MeetingText
from app.schemas.board_response import BoardActionItem, BoardResponse
from app.services.board_merge_service import BoardMergeService
from app.services.transcript_chunking_service import TranscriptChunkingService

_logger = get_logger("board")


class BoardService:
    def __init__(
        self,
        topics: TopicRepository,
        meetings: MeetingRepository,
        boards: BoardRepository,
        orchestrator: BoardOrchestrator,
        merger: BoardMergeService,
    ) -> None:
        self._topics = topics
        self._meetings = meetings
        self._boards = boards
        self._orchestrator = orchestrator
        self._merger = merger

    async def refresh(self, topic_id: int) -> BoardResponse:
        """Re-run the agents (old meetings come from the cache) and store the new board."""
        await self._require_topic(topic_id)
        meetings = await self._meetings.list_by_topic(topic_id)
        all_lines: list[MeetingLine] = []
        texts: list[MeetingText] = []
        for meeting in meetings:
            lines = await self._meetings.get_lines(meeting.id)
            all_lines.extend(lines)
            texts.append(
                MeetingText(
                    meeting_id=meeting.id,
                    title=meeting.title,
                    meeting_date=meeting.meeting_date,
                    speakers=list(dict.fromkeys(line.speaker for line in lines)),
                    lines=[TranscriptChunkingService.format_line(line) for line in lines],
                )
            )

        cached = await self._boards.get_extractions([m.id for m in meetings])
        # Each new extraction is saved at once, so a later failure (for example a rate limit
        # in the Stance agent) does not waste the tokens already spent.
        output = await self._orchestrator.run(
            BoardBuildInput(meetings=texts, cached=cached),
            on_extracted=self._boards.save_extraction,
        )

        board = self._merger.build(topic_id, meetings, all_lines, output)
        await self._boards.save_board(board)
        _logger.info(
            "Board for topic %s: %d decisions, %d actions, %d open, %d stances, %d changes",
            topic_id,
            len(board.decisions),
            len(board.action_items),
            len(board.open_items),
            len(board.stances),
            len(board.timeline),
        )
        return board

    async def get_board(self, topic_id: int) -> BoardResponse:
        await self._require_topic(topic_id)
        board = await self._boards.get_board(topic_id)
        if board is None:
            raise NotFoundError("The board for this topic has not been built yet.")
        return board

    async def my_action_items(self, topic_id: int, name: str) -> list[BoardActionItem]:
        """Only items owned by this person (case-insensitive full or first name match)."""
        board = await self.get_board(topic_id)
        wanted = " ".join(name.lower().split())
        return [
            item
            for item in board.action_items
            if item.owner
            and (item.owner.lower() == wanted or item.owner.lower().split()[0] == wanted)
        ]

    async def _require_topic(self, topic_id: int) -> None:
        if await self._topics.get_by_id(topic_id) is None:
            raise NotFoundError(f"Topic {topic_id} was not found.")
