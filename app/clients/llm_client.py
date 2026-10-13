"""Interface for any chat LLM provider."""

from typing import Any, Protocol


class LlmClient(Protocol):
    """Sends a system + user message and returns the reply parsed as a JSON object."""

    async def complete_json(self, system: str, user: str) -> dict[str, Any]: ...
