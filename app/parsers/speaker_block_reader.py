"""Shared reader for plain-text style transcripts (used by the .txt and .docx parsers)."""

import re

from app.parsers.base_transcript_parser import BaseTranscriptParser
from app.schemas.transcript_line import TranscriptLine

_TIME = r"\d{1,2}:\d{2}(?::\d{2})?(?:[.,]\d{1,3})?"
_SPEAKER = r"[^:\[\]]{1,60}?"
# [00:01:02] Speaker: text   |   00:01:02 Speaker: text
_TIMED_LINE = re.compile(rf"^\[?(?P<time>{_TIME})\]?\s+(?P<speaker>{_SPEAKER}):\s*(?P<text>.+)$")
# Speaker   00:01:02   (header line, the text follows on the next lines)
_HEADER_LINE = re.compile(rf"^(?P<speaker>[^\d:\[\]]{_SPEAKER})\s+\[?(?P<time>{_TIME})\]?$")
# Speaker: text   (no timestamp)
_PLAIN_LINE = re.compile(rf"^(?P<speaker>[A-Z]{_SPEAKER}):\s*(?P<text>.+)$")


class SpeakerBlockReader:
    """Reads lines in the common 'speaker + time + text' layouts."""

    def read(self, rows: list[str]) -> list[TranscriptLine]:
        """Group raw rows into speaker turns. Rows that match no layout continue the last turn."""
        turns: list[tuple[str, float | None, str]] = []
        pending_header: tuple[str, float | None] | None = None

        for raw in rows:
            row = raw.strip()
            if not row:
                continue
            timed = _TIMED_LINE.match(row)
            header = _HEADER_LINE.match(row)
            plain = _PLAIN_LINE.match(row)
            if timed:
                pending_header = None
                start = BaseTranscriptParser.parse_time(timed["time"])
                turns.append((timed["speaker"].strip(), start, timed["text"]))
            elif header:
                start = BaseTranscriptParser.parse_time(header["time"])
                pending_header = (header["speaker"].strip(), start)
            elif pending_header:
                turns.append((pending_header[0], pending_header[1], row))
                pending_header = None
            elif plain:
                turns.append((plain["speaker"].strip(), None, plain["text"]))
            elif turns:
                speaker, start, text = turns[-1]
                turns[-1] = (speaker, start, f"{text} {row}")

        return [
            TranscriptLine(
                line_number=index,
                speaker=speaker,
                start_seconds=start,
                text=BaseTranscriptParser.clean_text(text),
            )
            for index, (speaker, start, text) in enumerate(turns, start=1)
        ]
