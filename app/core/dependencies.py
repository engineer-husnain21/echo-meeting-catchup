"""Dependency wiring for FastAPI Depends. Concrete classes are created only here."""

from functools import lru_cache

from app.core.config import Settings, get_settings
from app.parsers.docx_transcript_parser import DocxTranscriptParser
from app.parsers.txt_transcript_parser import TxtTranscriptParser
from app.parsers.vtt_transcript_parser import VttTranscriptParser
from app.services.transcript_parsing_service import TranscriptParsingService


def get_app_settings() -> Settings:
    """Provide settings to routers and services."""
    return get_settings()


@lru_cache
def get_transcript_parsing_service() -> TranscriptParsingService:
    """Parsing service with one parser per supported file format."""
    settings = get_settings()
    return TranscriptParsingService(
        parsers=[VttTranscriptParser(), TxtTranscriptParser(), DocxTranscriptParser()],
        max_upload_bytes=settings.max_upload_mb * 1024 * 1024,
    )
