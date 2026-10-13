"""Parser for WebVTT transcripts exported by Teams or Zoom."""

import re

from app.parsers.base_transcript_parser import BaseTranscriptParser
from app.schemas.transcript_line import TranscriptLine

_CUE_TIMING = re.compile(r"^(?P<start>[\d:.,]+)\s+-->\s+(?P<end>[\d:.,]+)")
_VOICE_TAG = re.compile(r"<v(?:\.[^ >]*)?\s+(?P<speaker>[^>]+)>(?P<text>.*?)(?:</v>|$)", re.S)
_ANY_TAG = re.compile(r"<[^>]+>")
_SPEAKER_PREFIX = re.compile(r"^(?P<speaker>[^:]{1,60}):\s+(?P<text>.+)$", re.S)


class VttTranscriptParser(BaseTranscriptParser):
    """Reads cues: timing line, then text with a <v Speaker> tag or a 'Speaker:' prefix."""

    file_format = "vtt"
    extensions = (".vtt",)

    def parse(self, content: bytes) -> list[TranscriptLine]:
        text = self.decode(content)
        if not text.lstrip().startswith("WEBVTT"):
            raise ValueError("The file does not start with WEBVTT.")

        lines: list[TranscriptLine] = []
        for block in re.split(r"\n\s*\n", text):
            rows = [row for row in block.split("\n") if row.strip()]
            timing_index = next((i for i, row in enumerate(rows) if _CUE_TIMING.match(row)), None)
            if timing_index is None:
                continue
            timing = _CUE_TIMING.match(rows[timing_index])
            assert timing is not None
            cue_text = " ".join(rows[timing_index + 1 :])
            speaker, spoken = self._split_speaker(cue_text)
            spoken = self.clean_text(spoken)
            if not spoken:
                continue
            lines.append(
                TranscriptLine(
                    line_number=len(lines) + 1,
                    speaker=speaker,
                    start_seconds=self.parse_time(timing["start"]),
                    end_seconds=self.parse_time(timing["end"]),
                    text=spoken,
                )
            )
        return lines

    @staticmethod
    def _split_speaker(cue_text: str) -> tuple[str, str]:
        voice = _VOICE_TAG.search(cue_text)
        if voice:
            return voice["speaker"].strip(), _ANY_TAG.sub("", voice["text"])
        plain = _ANY_TAG.sub("", cue_text).strip()
        prefixed = _SPEAKER_PREFIX.match(plain)
        if prefixed:
            return prefixed["speaker"].strip(), prefixed["text"]
        return "Unknown speaker", plain
