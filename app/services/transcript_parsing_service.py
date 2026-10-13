"""Validates an uploaded transcript file and turns it into a ParsedTranscript."""

import hashlib
import re
from datetime import date
from pathlib import PurePath

from app.core.exceptions import ValidationError
from app.core.logging import get_logger
from app.parsers.base_transcript_parser import BaseTranscriptParser
from app.schemas.parsed_transcript import ParsedTranscript
from app.schemas.transcript_line import TranscriptLine

_logger = get_logger("parsing")
_FILENAME_DATE = re.compile(r"^(?P<date>\d{4}-\d{2}-\d{2})[_\- ]*(?P<title>.*)$")


class TranscriptParsingService:
    """Picks the parser by file extension and applies the upload rules."""

    def __init__(self, parsers: list[BaseTranscriptParser], max_upload_bytes: int) -> None:
        self._parsers = {ext: parser for parser in parsers for ext in parser.extensions}
        self._max_upload_bytes = max_upload_bytes

    @property
    def supported_extensions(self) -> list[str]:
        return sorted(self._parsers)

    def parse(self, filename: str, content: bytes, today: date | None = None) -> ParsedTranscript:
        """Parse one file. Raises ValidationError with a user-friendly message on bad input."""
        extension = PurePath(filename).suffix.lower()
        parser = self._parsers.get(extension)
        if parser is None:
            allowed = ", ".join(self.supported_extensions)
            raise ValidationError(f"'{filename}' is not a supported transcript. Use {allowed}.")
        if not content.strip():
            raise ValidationError(f"'{filename}' is empty.")
        if len(content) > self._max_upload_bytes:
            limit_mb = self._max_upload_bytes // (1024 * 1024)
            raise ValidationError(f"'{filename}' is larger than {limit_mb} MB.")

        try:
            lines = parser.parse(content)
        except ValueError as error:
            raise ValidationError(f"'{filename}' could not be read: {error}") from error
        if not lines:
            raise ValidationError(f"'{filename}' has no speaker lines that ECHO can read.")

        meeting_date, title = self._read_filename(filename, today or date.today())
        _logger.info("Parsed %s: %d lines, format=%s", filename, len(lines), parser.file_format)
        return ParsedTranscript(
            source_filename=PurePath(filename).name,
            file_format=parser.file_format,
            title=title,
            meeting_date=meeting_date,
            content_hash=self._hash_lines(lines),
            lines=lines,
        )

    @staticmethod
    def _read_filename(filename: str, fallback_date: date) -> tuple[date, str]:
        """Read 'YYYY-MM-DD_title.ext'. Without a date, the upload day is used."""
        stem = PurePath(filename).stem
        match = _FILENAME_DATE.match(stem)
        meeting_date, raw_title = fallback_date, stem
        if match:
            try:
                meeting_date = date.fromisoformat(match["date"])
                raw_title = match["title"] or "Meeting"
            except ValueError:
                pass
        title = re.sub(r"[_\-]+", " ", raw_title).strip().capitalize() or "Meeting"
        return meeting_date, title

    @staticmethod
    def _hash_lines(lines: list[TranscriptLine]) -> str:
        """Hash of the spoken content only, so the same meeting in another format is a duplicate."""
        normalized = "\n".join(f"{line.speaker.lower()}|{line.text.lower()}" for line in lines)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
