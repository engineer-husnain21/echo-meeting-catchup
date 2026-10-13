import pytest

from app.core.exceptions import EchoError
from app.core.prompt_loader import PromptLoader


def test_load_when_prompt_exists_returns_text() -> None:
    assert "Extractor agent" in PromptLoader().load("extractor_system")


def test_load_when_prompt_missing_raises() -> None:
    with pytest.raises(EchoError):
        PromptLoader().load("does_not_exist")
