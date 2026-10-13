from types import SimpleNamespace
from typing import Any

import httpx
import pytest
from openai import APIConnectionError

from app.clients.open_ai_compatible_embedding_client import OpenAiCompatibleEmbeddingClient
from app.core.exceptions import ProviderError


def _client(**kwargs: Any) -> OpenAiCompatibleEmbeddingClient:
    options = {"base_url": "https://example.test/v1", "api_key": "k", "model": "m"}
    options.update({"dimensions": 4, "batch_size": 2, "passage_task": "p", "query_task": "q"})
    options.update(kwargs)
    return OpenAiCompatibleEmbeddingClient(**options)


async def test_embed_when_many_texts_batches_and_sends_task(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    client = _client()
    sent: list[dict[str, Any]] = []

    async def fake_create(**kwargs: Any) -> SimpleNamespace:
        sent.append(kwargs)
        data = [SimpleNamespace(index=i, embedding=[float(i)]) for i in range(len(kwargs["input"]))]
        return SimpleNamespace(data=list(reversed(data)))

    monkeypatch.setattr(client._client.embeddings, "create", fake_create)
    vectors = await client.embed(["a", "b", "c"], purpose="query")
    assert vectors == [[0.0], [1.0], [0.0]]
    assert len(sent) == 2
    assert sent[0]["extra_body"] == {"task": "q"}
    assert sent[0]["dimensions"] == 4


async def test_embed_when_provider_fails_raises_provider_error(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    client = _client()

    async def failing_create(**_: Any) -> None:
        raise APIConnectionError(request=httpx.Request("POST", "https://example.test"))

    monkeypatch.setattr(client._client.embeddings, "create", failing_create)
    with pytest.raises(ProviderError):
        await client.embed(["a"], purpose="passage")
