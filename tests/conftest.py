"""Shared test fixtures. Tests never touch the real .env database or real APIs."""

from collections.abc import AsyncIterator, Iterator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.dependencies import (
    get_chunk_vector_repository,
    get_database,
    get_embedding_client,
    get_llm_client,
    get_speech_to_text_client,
    get_text_to_speech_client,
    get_transcript_chunking_service,
    get_transcript_parsing_service,
)
from app.db.database import Database

IN_MEMORY_DB = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(autouse=True)
def isolated_settings(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Point every test at an in-memory database and reset cached singletons."""
    monkeypatch.setenv("DATABASE_URL", IN_MEMORY_DB)
    monkeypatch.setenv("QDRANT_URL", "")  # in-memory Qdrant, never the real cluster
    monkeypatch.setenv("EMBEDDING_API_KEY", "")
    monkeypatch.setenv("LLM_API_KEY", "")
    monkeypatch.setenv("DEEPGRAM_API_KEY", "")
    _clear_caches()
    yield
    _clear_caches()


def _clear_caches() -> None:
    for cached in _CACHED:
        cached.cache_clear()


_CACHED = (
    get_settings,
    get_database,
    get_transcript_parsing_service,
    get_transcript_chunking_service,
    get_embedding_client,
    get_llm_client,
    get_chunk_vector_repository,
    get_speech_to_text_client,
    get_text_to_speech_client,
)


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    database = Database(IN_MEMORY_DB)
    await database.create_tables()
    async for session in database.session():
        yield session
    await database.dispose()
