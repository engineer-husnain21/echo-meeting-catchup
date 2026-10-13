import pytest

from app.parsers.base_transcript_parser import BaseTranscriptParser


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("00:00:04.000", 4.0),
        ("01:02:03.5", 3723.5),
        ("2:03", 123.0),
        ("0:00:07,250", 7.25),
        ("not a time", None),
    ],
)
def test_parse_time_when_formats_vary_returns_seconds(value: str, expected: float | None) -> None:
    assert BaseTranscriptParser.parse_time(value) == expected


def test_decode_when_bom_and_crlf_returns_clean_text() -> None:
    assert BaseTranscriptParser.decode("\ufeffa\r\nb".encode()) == "a\nb"
