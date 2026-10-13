import pytest
from qdrant_client import AsyncQdrantClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DuplicateError, NotFoundError, ProviderError, ValidationError
from app.parsers.docx_transcript_parser import DocxTranscriptParser
from app.parsers.txt_transcript_parser import TxtTranscriptParser
from app.parsers.vtt_transcript_parser import VttTranscriptParser
from app.repositories.chunk_vector_repository import ChunkVectorRepository
from app.repositories.meeting_repository import MeetingRepository
from app.repositories.topic_repository import TopicRepository
from app.services.meeting_upload_service import MeetingUploadService
from app.services.transcript_chunking_service import TranscriptChunkingService
from app.services.transcript_parsing_service import TranscriptParsingService
from tests.fakes.fake_embedding_client import FakeEmbeddingClient
from tests.sample_data import ATLAS_DIR, TEST_FILES_DIR

KICKOFF = ATLAS_DIR / "2026-09-28_kickoff.vtt"


def _service(
    session: AsyncSession, embeddings: FakeEmbeddingClient
) -> tuple[MeetingUploadService, ChunkVectorRepository]:
    parsers = [VttTranscriptParser(), TxtTranscriptParser(), DocxTranscriptParser()]
    vectors = ChunkVectorRepository(AsyncQdrantClient(location=":memory:"), "test", 64)
    service = MeetingUploadService(
        TopicRepository(session),
        MeetingRepository(session),
        TranscriptParsingService(parsers, max_upload_bytes=1024 * 1024),
        TranscriptChunkingService(6, 2),
        embeddings,
        vectors,
    )
    return service, vectors


async def test_upload_when_valid_stores_meeting_and_indexes_chunks(
    db_session: AsyncSession,
) -> None:
    embeddings = FakeEmbeddingClient(dimensions=64)
    service, vectors = _service(db_session, embeddings)
    topic = await TopicRepository(db_session).create("Atlas")

    result = await service.upload(topic.id, KICKOFF.name, KICKOFF.read_bytes())

    assert result.meeting.line_count == 25
    assert result.chunk_count == 6
    assert "Hussnain Razaq" in result.speakers
    assert embeddings.calls == [(6, "passage")]
    query = (await embeddings.embed(["PostgreSQL main database"], "query"))[0]
    assert await vectors.search(topic.id, query, 3)


async def test_upload_when_same_file_twice_raises_duplicate(db_session: AsyncSession) -> None:
    service, _ = _service(db_session, FakeEmbeddingClient(dimensions=64))
    topic = await TopicRepository(db_session).create("Atlas")
    await service.upload(topic.id, KICKOFF.name, KICKOFF.read_bytes())
    with pytest.raises(DuplicateError, match="already uploaded"):
        await service.upload(topic.id, "copy.vtt", KICKOFF.read_bytes())
    assert await MeetingRepository(db_session).count_by_topic(topic.id) == 1


async def test_upload_when_embeddings_fail_rolls_back_meeting(db_session: AsyncSession) -> None:
    service, _ = _service(db_session, FakeEmbeddingClient(dimensions=64, fail=True))
    topic = await TopicRepository(db_session).create("Atlas")
    with pytest.raises(ProviderError):
        await service.upload(topic.id, KICKOFF.name, KICKOFF.read_bytes())
    assert await MeetingRepository(db_session).count_by_topic(topic.id) == 0


async def test_upload_when_topic_missing_raises_not_found(db_session: AsyncSession) -> None:
    service, _ = _service(db_session, FakeEmbeddingClient(dimensions=64))
    with pytest.raises(NotFoundError):
        await service.upload(99, KICKOFF.name, KICKOFF.read_bytes())


async def test_upload_when_bad_file_raises_validation_and_stores_nothing(
    db_session: AsyncSession,
) -> None:
    service, _ = _service(db_session, FakeEmbeddingClient(dimensions=64))
    topic = await TopicRepository(db_session).create("Atlas")
    bad = TEST_FILES_DIR / "not-a-transcript.csv"
    with pytest.raises(ValidationError):
        await service.upload(topic.id, bad.name, bad.read_bytes())
    assert await MeetingRepository(db_session).count_by_topic(topic.id) == 0


async def test_upload_when_vector_store_unreachable_rolls_back_meeting(
    db_session: AsyncSession,
) -> None:
    parsers = [VttTranscriptParser(), TxtTranscriptParser(), DocxTranscriptParser()]
    unreachable = AsyncQdrantClient(url="http://127.0.0.1:9", timeout=1)
    service = MeetingUploadService(
        TopicRepository(db_session),
        MeetingRepository(db_session),
        TranscriptParsingService(parsers, max_upload_bytes=1024 * 1024),
        TranscriptChunkingService(6, 2),
        FakeEmbeddingClient(dimensions=64),
        ChunkVectorRepository(unreachable, "test", 64),
    )
    topic = await TopicRepository(db_session).create("Atlas")
    with pytest.raises(ProviderError, match="vector store"):
        await service.upload(topic.id, KICKOFF.name, KICKOFF.read_bytes())
    assert await MeetingRepository(db_session).count_by_topic(topic.id) == 0
