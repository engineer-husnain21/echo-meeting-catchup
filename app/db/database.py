"""Async SQLAlchemy engine, session factory and table creation."""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    """Base class for all DB entities."""


class Database:
    """Owns the engine and hands out sessions."""

    def __init__(self, database_url: str) -> None:
        options: dict[str, object] = {}
        if ":memory:" in database_url:
            # One shared connection so every session sees the same in-memory database.
            options = {"poolclass": StaticPool, "connect_args": {"check_same_thread": False}}
        self._engine: AsyncEngine = create_async_engine(database_url, **options)
        self._session_factory = async_sessionmaker(self._engine, expire_on_commit=False)

    async def create_tables(self) -> None:
        """Create all tables that do not exist yet."""
        from app import models  # noqa: F401  (registers the entities on Base)

        async with self._engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    async def session(self) -> AsyncIterator[AsyncSession]:
        """Yield one session per request."""
        async with self._session_factory() as session:
            yield session

    async def dispose(self) -> None:
        await self._engine.dispose()
