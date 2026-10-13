"""Dependency wiring for FastAPI Depends. Concrete classes are created only here."""

from collections.abc import AsyncIterator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.database import Database
from app.parsers.docx_transcript_parser import DocxTranscriptParser
from app.parsers.txt_transcript_parser import TxtTranscriptParser
from app.parsers.vtt_transcript_parser import VttTranscriptParser
from app.repositories.meeting_repository import MeetingRepository
from app.repositories.topic_repository import TopicRepository
from app.services.topic_service import TopicService
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
