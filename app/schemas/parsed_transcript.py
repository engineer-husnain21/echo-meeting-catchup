"""A transcript after parsing, ready to be chunked and stored."""

from datetime import date

from pydantic import BaseModel, computed_field

from app.schemas.transcript_line import TranscriptLine


class ParsedTranscript(BaseModel):
    """Meeting metadata plus the ordered transcript lines."""

    source_filename: str
    file_format: str
    title: str
    meeting_date: date
    content_hash: str
    lines: list[TranscriptLine]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def speakers(self) -> list[str]:
        """Speakers in order of first appearance."""
        return list(dict.fromkeys(line.speaker for line in self.lines))

    @computed_field  # type: ignore[prop-decorator]
    @property
    def duration_seconds(self) -> float:
        """Approximate meeting length from the last timestamp."""
        times = [t for line in self.lines for t in (line.end_seconds, line.start_seconds) if t]
        return max(times, default=0.0)
