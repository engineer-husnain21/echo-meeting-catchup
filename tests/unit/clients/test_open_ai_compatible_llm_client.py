from types import SimpleNamespace
from typing import Any

import httpx
import pytest
from openai import APIConnectionError

from app.clients.open_ai_compatible_llm_client import OpenAiCompatibleLlmClient
from app.core.exceptions import ProviderError


def _client() -> OpenAiCompatibleLlmClient:
    return OpenAiCompatibleLlmClient(
        base_url="https://example.test/v1",
        api_key="k",
        model="m",
        max_tokens=100,
        timeout_seconds=5,
        reasoning_effort="low",
    )


def _reply(text: str) -> SimpleNamespace:
    message = SimpleNamespace(content=text)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)], usage=None)


async def test_complete_json_when_fenced_json_returns_dict(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    client = _client()
    sent: list[dict[str, Any]] = []

    async def fake_create(**kwargs: Any) -> SimpleNamespace:
        sent.append(kwargs)
        return _reply('```json\n{"ok": true}\n```')

    monkeypatch.setattr(client._client.chat.completions, "create", fake_create)
    assert await client.complete_json("sys", "user") == {"ok": True}
    assert sent[0]["extra_body"] == {"reasoning_effort": "low"}
    assert sent[0]["response_format"] == {"type": "json_object"}


async def test_complete_json_when_never_json_raises_after_retry(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    client = _client()
    calls = []

    async def fake_create(**_: Any) -> SimpleNamespace:
        calls.append(1)
        return _reply("sorry, no json")

    monkeypatch.setattr(client._client.chat.completions, "create", fake_create)
    with pytest.raises(ProviderError):
        await client.complete_json("sys", "user")
    assert len(calls) == 2


async def test_complete_json_when_provider_down_raises_provider_error(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    client = _client()

    async def failing(**_: Any) -> None:
        raise APIConnectionError(request=httpx.Request("POST", "https://example.test"))

    monkeypatch.setattr(client._client.chat.completions, "create", failing)
    with pytest.raises(ProviderError):
        await client.complete_json("sys", "user")


async def test_complete_json_when_rate_limited_waits_and_retries(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from openai import RateLimitError

    import app.clients.open_ai_compatible_llm_client as module

    client = _client()
    waits: list[float] = []
    calls: list[int] = []

    async def fake_sleep(seconds: float) -> None:
        waits.append(seconds)

    async def fake_create(**_: Any) -> SimpleNamespace:
        calls.append(1)
        if len(calls) == 1:
            response = httpx.Response(
                429, headers={"retry-after": "2"}, request=httpx.Request("POST", "https://x")
            )
            raise RateLimitError("rate limited", response=response, body=None)
        return _reply('{"ok": 1}')

    monkeypatch.setattr(module.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(client._client.chat.completions, "create", fake_create)
    assert await client.complete_json("s", "u") == {"ok": 1}
    assert waits == [2.0]
