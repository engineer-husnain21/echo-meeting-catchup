from app.schemas.narrator_output import NarratorOutput


def test_validate_when_text_under_other_key_still_reads_it() -> None:
    output = NarratorOutput.model_validate({"script": " Hi \n there ", "citations": {"x": 1}})
    assert output.briefing == "Hi there"
    assert output.citations == []  # broken citation dropped


def test_validate_when_empty_reply_gives_empty_briefing() -> None:
    assert NarratorOutput.model_validate({}).briefing == ""
