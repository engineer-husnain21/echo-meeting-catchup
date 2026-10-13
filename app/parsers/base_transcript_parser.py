"""Base class for transcript parsers. One subclass per file format."""

import re
from abc import ABC, abstractmethod

from app.schemas.transcript_line import TranscriptLine

# Accepts h:mm:ss, hh:mm:ss, mm:ss with an optional .mmm or ,mmm part.
_TIME_PATTERN = re.compile(r"^(?:(\d{1,2}):)?(\d{1,2}):(\d{2})(?:[.,](\d{1,3}))?$")


class BaseTranscriptParser(ABC):
    """Turns raw file bytes into transcript lines."""

    file_format: str
    extensions: tuple[str, ...]

    @abstractmethod
    def parse(self, content: bytes) -> list[TranscriptLine]:
        """Return the transcript lines. Raise ValueError if the content cannot be read."""

    @staticmethod
    def parse_time(value: str) -> float | None:
        """Convert a timestamp like 01:02:03.500 or 2:03 to seconds."""
        match = _TIME_PATTERN.match(value.strip())
        if not match:
            return None
        hours, minutes, seconds, fraction = match.groups()
        total = float(int(hours or 0) * 3600 + int(minutes) * 60 + int(seconds))
        if fraction:
            total += int(fraction.ljust(3, "0")) / 1000
        return total

    @staticmethod
    def decode(content: bytes) -> str:
        """Decode text files, accepting UTF-8 with or without BOM and Windows line endings."""
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = content.decode("cp1252", errors="replace")
        return text.replace("\r\n", "\n").replace("\r", "\n")

    @staticmethod
    def clean_text(text: str) -> str:
        """Collapse whitespace inside a spoken line."""
        return " ".join(text.split())
