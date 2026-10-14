from typing import Any

import pytest
from qdrant_client import AsyncQdrantClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.answer_agent import AnswerAgent
from app.clients.embedding_client import EmbeddingPurpose
from app.core.exceptions import NotFoundError
from app.core.prompt_loader import PromptLoader
from app.orchestrators.answer_orchestrator import AnswerOrchestrator
from app.parsers.docx_transcript_parser import DocxTranscriptParser
from app.parsers.txt_transcript_parser import TxtTranscriptParser
from app.parsers.vtt_transcript_parser import VttTranscriptParser
from app.repositories.board_repository import BoardRepository
from app.repositories.chunk_vector_repository import ChunkVectorRepository
from app.repositories.meeting_repository import MeetingRepository
from app.repositories.topic_repository import TopicRepository
from app.schemas.ask_question_request import AskQuestionRequest
from app.schemas.chat_turn import ChatTurn
from app.services.meeting_upload_service import MeetingUploadService
from app.services.question_service import NO_MEETINGS, NOT_DISCUSSED, QuestionService
from app.services.transcript_chunking_service import TranscriptChunkingService
from app.services.transcript_parsing_service import TranscriptParsingService
from tests.fakes.fake_embedding_client import FakeEmbeddingClient
from tests.fakes.fake_llm_client import FakeLlmClient
from tests.sample_data import ATLAS_DIR

KICKOFF = ATLAS_DIR / "2026-09-28_kickoff.vtt"


class RecordingEmbeddingClient(FakeEmbeddingClient):
    def __init__(self) -> None:
        super().__init__(dimensions=64)
        self.texts: list[str] = []

    async def embed(self, texts: list[str], purpose: EmbeddingPurpose) -> list[list[float]]:
        self.texts.extend(texts)
        return await super().embed(texts, purpose)


async def _setup(
    session: AsyncSession, replies: list[dict[str, Any]], upload: bool = True
) -> tuple[QuestionService, FakeLlmClient, RecordingEmbeddingClient, int]:
    embeddings = RecordingEmbeddingClient()
    vectors = ChunkVectorRepository(AsyncQdrantClient(location=":memory:"), "test", 64)
    topic = await TopicRepository(session).create("Atlas")
    if upload:
        parsers = [VttTranscriptParser(), TxtTranscriptParser(), DocxTranscriptParser()]
        uploader = MeetingUploadService(
            TopicRepository(session),
            MeetingRepository(session),
            TranscriptParsingService(parsers, max_upload_bytes=1024 * 1024),
            TranscriptChunkingService(6, 2),
            embeddings,
            vectors,
        )
        await uploader.upload(topic.id, KICKOFF.name, KICKOFF.read_bytes())
    embeddings.texts.clear()
    llm = FakeLlmClient(replies)
    service = QuestionService(
        TopicRepository(session),
        MeetingRepository(session),
        BoardRepository(session),
        embeddings,
        vectors,
        AnswerOrchestrator(AnswerAgent(llm, PromptLoader())),
        top_k=10,  # the kickoff has 6 chunks, so every line is shown
        history_turns=4,
    )
    return service, llm, embeddings, topic.id


async def test_ask_when_answer_cites_real_and_invented_lines_keeps_only_real_quotes(
    db_session: AsyncSession,
) -> None:
    reply = {
        "status": "answered",
        "answer": "PostgreSQL.",
        "citations": [{"meeting_id": 1, "line": 15}, {"meeting_id": 1, "line": 99}, "M7 L1"],
    }
    service, _, _, topic_id = await _setup(db_session, [reply])
    response = await service.ask(topic_id, AskQuestionRequest(question="Which database?"))
    assert response.status == "answered"
    assert [(q.line, q.speaker) for q in response.citations] == [(15, "Maya Chen")]
    assert "PostgreSQL is our main database" in response.citations[0].text
    assert response.citations[0].meeting_title


async def test_ask_when_no_citation_is_valid_replies_not_discussed(
    db_session: AsyncSession,
) -> None:
    reply = {"status": "answered", "answer": "Kubernetes.", "citations": ["M1 L99"]}
    service, _, _, topic_id = await _setup(db_session, [reply])
    response = await service.ask(topic_id, AskQuestionRequest(question="Which cloud?"))
    assert response.status == "not_discussed"
    assert response.answer == NOT_DISCUSSED and response.citations == []


async def test_ask_when_agent_says_not_discussed_keeps_its_answer(
    db_session: AsyncSession,
) -> None:
    reply = {"status": "not_discussed", "answer": "That wasn't discussed in these meetings."}
    service, _, _, topic_id = await _setup(db_session, [reply])
    response = await service.ask(topic_id, AskQuestionRequest(question="Office party?"))
    assert response.status == "not_discussed" and response.answer.startswith("That wasn't")


async def test_ask_when_question_vague_returns_clarify_without_citations(
    db_session: AsyncSession,
) -> None:
    reply = {
        "status": "clarify",
        "answer": "Do you mean the ingestion API or the CI pipeline?",
        "citations": ["M1 L18"],
    }
    service, _, _, topic_id = await _setup(db_session, [reply])
    response = await service.ask(topic_id, AskQuestionRequest(question="When is it due?"))
    assert response.status == "clarify" and response.citations == []
    assert response.answer.endswith("?")


async def test_ask_when_follow_up_searches_with_earlier_question_and_limits_history(
    db_session: AsyncSession,
) -> None:
    service, llm, embeddings, topic_id = await _setup(db_session, [{"status": "clarify"}])
    history = [ChatTurn(role="user", text=f"old question {n}") for n in range(5)]
    history.append(ChatTurn(role="echo", text="Maya decided it."))
    await service.ask(
        topic_id, AskQuestionRequest(question="Why?", history=history, user_name="Hussnain")
    )
    assert embeddings.texts == ["old question 3\nold question 4\nWhy?"]
    user = llm.calls[0][1]
    assert "old question 1" not in user  # only the last 4 turns are kept
    assert "User: old question 2" in user and "ECHO: Maya decided it." in user
    assert "Person asking: Hussnain" in user


async def test_ask_when_topic_has_no_meetings_answers_without_llm(
    db_session: AsyncSession,
) -> None:
    service, llm, embeddings, topic_id = await _setup(db_session, [], upload=False)
    response = await service.ask(topic_id, AskQuestionRequest(question="Anything?"))
    assert response.answer == NO_MEETINGS
    assert llm.calls == [] and embeddings.texts == []


async def test_ask_when_topic_missing_raises_not_found(db_session: AsyncSession) -> None:
    service, _, _, _ = await _setup(db_session, [], upload=False)
    with pytest.raises(NotFoundError):
        await service.ask(99, AskQuestionRequest(question="Anything?"))
