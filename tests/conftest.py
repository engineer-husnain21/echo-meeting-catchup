"""Shared test fixtures. Tests never touch the real .env database or real APIs."""

from collections.abc import AsyncIterator, Iterator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.dependencies import get_database, get_transcript_parsing_service
from app.db.database import Database

IN_MEMORY_DB = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(autouse=True)
def isolated_settings(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Point every test at an in-memory database and reset cached singletons."""
    monkeypatch.setenv("DATABASE_URL", IN_MEMORY_DB)
    for cached in (get_settings, get_database, get_transcript_parsing_service):
        cached.cache_clear()
    yield
    for cached in (get_settings, get_database, get_transcript_parsing_service):
        cached.cache_clear()


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    database = Database(IN_MEMORY_DB)
    await database.create_tables()
    async for session in database.session():
        yield session
    await database.dispose()
