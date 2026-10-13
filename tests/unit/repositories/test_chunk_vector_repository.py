from datetime import date

from qdrant_client import AsyncQdrantClient

from app.repositories.chunk_vector_repository import ChunkVectorRepository
from app.schemas.transcript_chunk import TranscriptChunk
from tests.fakes.fake_embedding_client import FakeEmbeddingClient


def _chunk(topic_id: int, meeting_id: int, index: int, text: str) -> TranscriptChunk:
    return TranscriptChunk(
        topic_id=topic_id,
        meeting_id=meeting_id,
        meeting_title="Kickoff",
        meeting_date=date(2026, 9, 28),
        chunk_index=index,
        first_line=1,
        last_line=6,
        start_seconds=4.0,
        speakers=["Maya Chen"],
        text=text,
    )


async def test_search_when_two_topics_returns_only_requested_topic() -> None:
    embed = FakeEmbeddingClient(dimensions=64)
    repo = ChunkVectorRepository(AsyncQdrantClient(location=":memory:"), "test", 64)
    chunks = [
        _chunk(1, 10, 0, "we picked postgresql as the database"),
        _chunk(1, 10, 1, "hosting budget is four hundred dollars"),
        _chunk(2, 20, 0, "postgresql database for another project"),
    ]
    await repo.upsert(chunks, await embed.embed([c.text for c in chunks], "passage"))

    query = (await embed.embed(["which database"], "query"))[0]
    hits = await repo.search(topic_id=1, vector=query, limit=5)
    assert {hit.chunk.topic_id for hit in hits} == {1}
    assert hits[0].chunk.text.startswith("we picked postgresql")


async def test_delete_meeting_when_called_removes_its_chunks() -> None:
    embed = FakeEmbeddingClient(dimensions=64)
    repo = ChunkVectorRepository(AsyncQdrantClient(location=":memory:"), "test", 64)
    chunk = _chunk(1, 10, 0, "hello")
    await repo.upsert([chunk], await embed.embed([chunk.text], "passage"))
    await repo.delete_meeting(10)
    assert await repo.search(1, (await embed.embed(["hello"], "query"))[0], 5) == []
