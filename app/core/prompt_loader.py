"""Loads prompt text from app/prompts/*.md. Prompts are never written inside Python files."""

from functools import cache
from pathlib import Path

from app.core.exceptions import EchoError

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


class PromptLoader:
    def __init__(self, prompts_dir: Path = PROMPTS_DIR) -> None:
        self._prompts_dir = prompts_dir

    def load(self, name: str) -> str:
        """Return the prompt text for '<name>.md'."""
        return _read(self._prompts_dir / f"{name}.md")


@cache
def _read(path: Path) -> str:
    if not path.is_file():
        raise EchoError(f"Prompt file '{path.name}' is missing.")
    return path.read_text(encoding="utf-8").strip()
