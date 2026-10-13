"""Parser for plain-text transcripts."""

from app.parsers.base_transcript_parser import BaseTranscriptParser
from app.parsers.speaker_block_reader import SpeakerBlockReader
from app.schemas.transcript_line import TranscriptLine


class TxtTranscriptParser(BaseTranscriptParser):
    """Reads '[hh:mm:ss] Speaker: text', 'Speaker  hh:mm:ss' + text, or 'Speaker: text'."""

    file_format = "txt"
    extensions = (".txt",)

    def __init__(self, reader: SpeakerBlockReader | None = None) -> None:
        self._reader = reader or SpeakerBlockReader()

    def parse(self, content: bytes) -> list[TranscriptLine]:
        return self._reader.read(self.decode(content).split("\n"))
