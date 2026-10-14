"""Builds the spoken "catch me up" briefing of a topic from its stored board."""

import time

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.orchestrators.answer_orchestrator import AnswerOrchestrator
from app.repositories.board_repository import BoardRepository
from app.repositories.meeting_repository import MeetingRepository
from app.repositories.topic_repository import TopicRepository
from app.schemas.board_response import BoardMeeting
from app.schemas.briefing_build_input import BriefingBuildInput
from app.schemas.briefing_response import BriefingResponse
from app.services.citation_service import CitationService

_logger = get_logger("briefing")
MAX_BRIEFING_CITATIONS = 8


class BriefingService:
    def __init__(
        self,
        topics: TopicRepository,
        meetings: MeetingRepository,
        boards: BoardRepository,
        orchestrator: AnswerOrchestrator,
        citations: CitationService,
    ) -> None:
        self._topics = topics
        self._meetings = meetings
        self._boards = boards
        self._orchestrator = orchestrator
        self._citations = citations

    async def brief(self, topic_id: int, user_name: str | None) -> BriefingResponse:
        started = time.perf_counter()
        if await self._topics.get_by_id(topic_id) is None:
            raise NotFoundError(f"Topic {topic_id} was not found.")
        board = await self._boards.get_board(topic_id)
        if board is None:
            raise NotFoundError("The board for this topic has not been built yet.")
        meetings = await self._meetings.list_by_topic(topic_id)

        result = await self._orchestrator.brief(
            BriefingBuildInput(
                user_name=user_name,
                meetings=[
                    BoardMeeting(id=m.id, title=m.title, meeting_date=m.meeting_date)
                    for m in meetings
                ],
                board=board,
            )
        )
        if not result.output.briefing:
            raise NotFoundError("ECHO could not put together a briefing for this topic.")
        quotes = await self._citations.quotes(
            result.output.citations, result.shown_lines, meetings, limit=MAX_BRIEFING_CITATIONS
        )
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        _logger.info("Topic %s briefing: %d citations, %d ms", topic_id, len(quotes), elapsed_ms)
        return BriefingResponse(
            briefing=result.output.briefing, citations=quotes, elapsed_ms=elapsed_ms
        )
