"""Parser for Word (.docx) transcripts."""

import io
import zipfile

from docx import Document

from app.parsers.base_transcript_parser import BaseTranscriptParser
from app.parsers.speaker_block_reader import SpeakerBlockReader
from app.schemas.transcript_line import TranscriptLine


class DocxTranscriptParser(BaseTranscriptParser):
    """Reads the paragraphs of a .docx file with the same layouts as the .txt parser."""

    file_format = "docx"
    extensions = (".docx",)

    def __init__(self, reader: SpeakerBlockReader | None = None) -> None:
        self._reader = reader or SpeakerBlockReader()

    def parse(self, content: bytes) -> list[TranscriptLine]:
        try:
            document = Document(io.BytesIO(content))
        except (zipfile.BadZipFile, KeyError, ValueError) as error:
            raise ValueError("The Word file is corrupt or not a real .docx file.") from error
        rows: list[str] = []
        for paragraph in document.paragraphs:
            rows.extend(paragraph.text.split("\n"))
        return self._reader.read(rows)
