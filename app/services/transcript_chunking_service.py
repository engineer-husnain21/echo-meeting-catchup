"""Splits a meeting into overlapping groups of speaker lines for retrieval."""

from app.models.meeting import Meeting
from app.models.meeting_line import MeetingLine
from app.schemas.transcript_chunk import TranscriptChunk


class TranscriptChunkingService:
    def __init__(self, lines_per_chunk: int, overlap_lines: int) -> None:
        if lines_per_chunk < 1 or not 0 <= overlap_lines < lines_per_chunk:
            raise ValueError("Need lines_per_chunk >= 1 and 0 <= overlap < lines_per_chunk.")
        self._size = lines_per_chunk
        self._step = lines_per_chunk - overlap_lines

    def chunk(self, meeting: Meeting, lines: list[MeetingLine]) -> list[TranscriptChunk]:
        chunks: list[TranscriptChunk] = []
        for start in range(0, len(lines), self._step):
            window = lines[start : start + self._size]
            chunks.append(
                TranscriptChunk(
                    topic_id=meeting.topic_id,
                    meeting_id=meeting.id,
                    meeting_title=meeting.title,
                    meeting_date=meeting.meeting_date,
                    chunk_index=len(chunks),
                    first_line=window[0].line_number,
                    last_line=window[-1].line_number,
                    start_seconds=window[0].start_seconds,
                    speakers=list(dict.fromkeys(line.speaker for line in window)),
                    text="\n".join(self._format_line(line) for line in window),
                )
            )
            if start + self._size >= len(lines):
                break
        return chunks

    @staticmethod
    def _format_line(line: MeetingLine) -> str:
        """'[L12 05:31] Maya Chen: text' so the LLM can cite exact lines."""
        if line.start_seconds is None:
            return f"[L{line.line_number}] {line.speaker}: {line.text}"
        minutes, seconds = divmod(int(line.start_seconds), 60)
        hours, minutes = divmod(minutes, 60)
        stamp = f"{hours}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes:02d}:{seconds:02d}"
        return f"[L{line.line_number} {stamp}] {line.speaker}: {line.text}"
