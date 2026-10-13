"""Fake LLM: returns queued JSON replies and records what it was asked. No network."""

from typing import Any

from app.core.exceptions import ProviderError


class FakeLlmClient:
    def __init__(self, replies: list[dict[str, Any]] | None = None, fail: bool = False) -> None:
        self.replies = list(replies or [])
        self.fail = fail
        self.calls: list[tuple[str, str]] = []

    async def complete_json(self, system: str, user: str) -> dict[str, Any]:
        self.calls.append((system, user))
        if self.fail:
            raise ProviderError("The language model is not available right now.")
        return self.replies.pop(0) if self.replies else {}
