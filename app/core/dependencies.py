"""Dependency wiring for FastAPI Depends. Concrete classes are created only here."""

from collections.abc import AsyncIterator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from qdrant_client import AsyncQdrantClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.answer_agent import AnswerAgent
from app.agents.extractor_agent import ExtractorAgent
from app.agents.stance_agent import StanceAgent
from app.agents.timeline_agent import TimelineAgent
from app.clients.embedding_client import EmbeddingClient
from app.clients.llm_client import LlmClient
from app.clients.open_ai_compatible_embedding_client import OpenAiCompatibleEmbeddingClient
from app.clients.open_ai_compatible_llm_client import OpenAiCompatibleLlmClient
from app.core.config import Settings, get_settings
from app.core.prompt_loader import PromptLoader
from app.db.database import Database
from app.orchestrators.answer_orchestrator import AnswerOrchestrator
from app.orchestrators.board_orchestrator import BoardOrchestrator
from app.parsers.docx_transcript_parser import DocxTranscriptParser
from app.parsers.txt_transcript_parser import TxtTranscriptParser
from app.parsers.vtt_transcript_parser import VttTranscriptParser
from app.repositories.board_repository import BoardRepository
from app.repositories.chunk_vector_repository import ChunkVectorRepository
from app.repositories.meeting_repository import MeetingRepository
from app.repositories.topic_repository import TopicRepository
from app.services.board_merge_service import BoardMergeService
from app.services.board_service import BoardService
from app.services.meeting_service import MeetingService
from app.services.meeting_upload_service import MeetingUploadService
from app.services.question_service import QuestionService
from app.services.topic_service import TopicService
from app.services.transcript_chunking_service import TranscriptChunkingService
from app.services.transcript_parsing_service import TranscriptParsingService


def get_app_settings() -> Settings:
    """Provide settings to routers and services."""
    return get_settings()


@lru_cache
def get_database() -> Database:
    """One Database (engine) for the whole app."""
    return Database(get_settings().database_url)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async for session in get_database().session():
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_db_session)]


@lru_cache
def get_transcript_parsing_service() -> TranscriptParsingService:
    """Parsing service with one parser per supported file format."""
    settings = get_settings()
    return TranscriptParsingService(
        parsers=[VttTranscriptParser(), TxtTranscriptParser(), DocxTranscriptParser()],
        max_upload_bytes=settings.max_upload_mb * 1024 * 1024,
    )


def get_topic_service(session: SessionDep) -> TopicService:
    return TopicService(TopicRepository(session), MeetingRepository(session))


@lru_cache
def get_embedding_client() -> EmbeddingClient:
    settings = get_settings()
    return OpenAiCompatibleEmbeddingClient(
        base_url=settings.embedding_base_url,
        api_key=settings.embedding_api_key.get_secret_value(),
        model=settings.embedding_model,
        dimensions=settings.embedding_dimensions,
        batch_size=settings.embedding_batch_size,
        passage_task=settings.embedding_passage_task,
        query_task=settings.embedding_query_task,
    )


@lru_cache
def get_chunk_vector_repository() -> ChunkVectorRepository:
    settings = get_settings()
    client = AsyncQdrantClient(
        url=settings.qdrant_url or None,
        api_key=settings.qdrant_api_key.get_secret_value() or None,
        location=None if settings.qdrant_url else ":memory:",
        timeout=settings.qdrant_timeout_seconds,
    )
    return ChunkVectorRepository(client, settings.qdrant_collection, settings.embedding_dimensions)


@lru_cache
def get_transcript_chunking_service() -> TranscriptChunkingService:
    settings = get_settings()
    return TranscriptChunkingService(settings.chunk_lines, settings.chunk_overlap_lines)


def get_meeting_upload_service(
    session: SessionDep,
    parser: Annotated[TranscriptParsingService, Depends(get_transcript_parsing_service)],
    chunker: Annotated[TranscriptChunkingService, Depends(get_transcript_chunking_service)],
    embeddings: Annotated[EmbeddingClient, Depends(get_embedding_client)],
    vectors: Annotated[ChunkVectorRepository, Depends(get_chunk_vector_repository)],
) -> MeetingUploadService:
    return MeetingUploadService(
        TopicRepository(session), MeetingRepository(session), parser, chunker, embeddings, vectors
    )


def get_meeting_service(session: SessionDep) -> MeetingService:
    return MeetingService(TopicRepository(session), MeetingRepository(session))


@lru_cache
def get_llm_client() -> LlmClient:
    settings = get_settings()
    return OpenAiCompatibleLlmClient(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key.get_secret_value(),
        model=settings.llm_model,
        max_tokens=settings.llm_max_tokens,
        timeout_seconds=settings.llm_timeout_seconds,
        reasoning_effort=settings.llm_reasoning_effort,
        rate_limit_retries=settings.llm_rate_limit_retries,
    )


def get_board_orchestrator(
    llm: Annotated[LlmClient, Depends(get_llm_client)],
) -> BoardOrchestrator:
    settings = get_settings()
    prompts = PromptLoader()
    return BoardOrchestrator(
        extractor=ExtractorAgent(llm, prompts),
        stance=StanceAgent(llm, prompts),
        timeline=TimelineAgent(llm, prompts),
        window_lines=settings.extract_window_lines,
        stance_max_lines=settings.stance_max_lines,
    )


def get_board_service(
    session: SessionDep,
    orchestrator: Annotated[BoardOrchestrator, Depends(get_board_orchestrator)],
) -> BoardService:
    return BoardService(
        TopicRepository(session),
        MeetingRepository(session),
        BoardRepository(session),
        orchestrator,
        BoardMergeService(),
    )


def get_answer_orchestrator(
    llm: Annotated[LlmClient, Depends(get_llm_client)],
) -> AnswerOrchestrator:
    return AnswerOrchestrator(AnswerAgent(llm, PromptLoader()))


def get_question_service(
    session: SessionDep,
    embeddings: Annotated[EmbeddingClient, Depends(get_embedding_client)],
    vectors: Annotated[ChunkVectorRepository, Depends(get_chunk_vector_repository)],
    orchestrator: Annotated[AnswerOrchestrator, Depends(get_answer_orchestrator)],
) -> QuestionService:
    settings = get_settings()
    return QuestionService(
        TopicRepository(session),
        MeetingRepository(session),
        BoardRepository(session),
        embeddings,
        vectors,
        orchestrator,
        top_k=settings.qa_top_k,
        history_turns=settings.qa_history_turns,
    )
