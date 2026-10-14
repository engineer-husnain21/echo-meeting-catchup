"""Answers a spoken or typed question about a topic, with grounded citations.

Flow: find matching chunks (embeddings + vector store), load the stored board, let the
orchestrator run the Answer agent, then let CitationService keep only grounded citations.
"""

import time

from app.clients.embedding_client import EmbeddingClient
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.models.meeting import Meeting
from app.orchestrators.answer_orchestrator import AnswerOrchestrator
from app.repositories.board_repository import BoardRepository
from app.repositories.chunk_vector_repository import ChunkVectorRepository
from app.repositories.meeting_repository import MeetingRepository
from app.repositories.topic_repository import TopicRepository
from app.schemas.answer_build_input import AnswerBuildInput
from app.schemas.answer_output import AnswerOutput
from app.schemas.answer_response import AnswerResponse
from app.schemas.ask_question_request import AskQuestionRequest
from app.schemas.board_response import BoardMeeting
from app.schemas.line_ref import LineRef
from app.services.citation_service import CitationService

_logger = get_logger("questions")
NOT_DISCUSSED = "That wasn't discussed in these meetings."
NO_MEETINGS = "There are no meetings in this topic yet. Upload a transcript first."
_RETRIEVAL_TURNS = 2  # earlier user questions added to the search text for follow-ups


class QuestionService:
    def __init__(
        self,
        topics: TopicRepository,
        meetings: MeetingRepository,
        boards: BoardRepository,
        embeddings: EmbeddingClient,
        vectors: ChunkVectorRepository,
        orchestrator: AnswerOrchestrator,
        citations: CitationService,
        top_k: int,
        history_turns: int,
    ) -> None:
        self._topics = topics
        self._meetings = meetings
        self._boards = boards
        self._embeddings = embeddings
        self._vectors = vectors
        self._orchestrator = orchestrator
        self._citations = citations
        self._top_k = top_k
        self._history_turns = history_turns

    async def ask(self, topic_id: int, request: AskQuestionRequest) -> AnswerResponse:
        started = time.perf_counter()
        if await self._topics.get_by_id(topic_id) is None:
            raise NotFoundError(f"Topic {topic_id} was not found.")
        meetings = await self._meetings.list_by_topic(topic_id)
        if not meetings:
            return AnswerResponse(status="not_discussed", answer=NO_MEETINGS, elapsed_ms=0)

        history = request.history[-self._history_turns :] if self._history_turns else []
        earlier = [t.text for t in history if t.role == "user"][-_RETRIEVAL_TURNS:]
        search_text = "\n".join([*earlier, request.question])
        vector = (await self._embeddings.embed([search_text], purpose="query"))[0]
        chunks = await self._vectors.search(topic_id, vector, self._top_k)

        result = await self._orchestrator.run(
            AnswerBuildInput(
                question=request.question,
                user_name=request.user_name,
                history=history,
                meetings=[
                    BoardMeeting(id=m.id, title=m.title, meeting_date=m.meeting_date)
                    for m in meetings
                ],
                chunks=chunks,
                board=await self._boards.get_board(topic_id),
            )
        )
        response = await self._ground(result.output, result.shown_lines, meetings)
        response.elapsed_ms = int((time.perf_counter() - started) * 1000)
        _logger.info(
            "Topic %s question answered: status=%s, %d citations, %d ms",
            topic_id,
            response.status,
            len(response.citations),
            response.elapsed_ms,
        )
        return response

    async def _ground(
        self, output: AnswerOutput, shown: list[LineRef], meetings: list[Meeting]
    ) -> AnswerResponse:
        if output.status == "clarify":
            return AnswerResponse(status="clarify", answer=output.answer, elapsed_ms=0)

        quotes = await self._citations.quotes(output.citations, shown, meetings)
        if output.status == "not_discussed":
            return AnswerResponse(
                status="not_discussed",
                answer=output.answer or NOT_DISCUSSED,
                citations=quotes,
                elapsed_ms=0,
            )
        if not quotes or not output.answer:
            _logger.warning("Answer had no valid citations, replied 'not discussed' instead")
            return AnswerResponse(status="not_discussed", answer=NOT_DISCUSSED, elapsed_ms=0)
        return AnswerResponse(
            status="answered", answer=output.answer, citations=quotes, elapsed_ms=0
        )
