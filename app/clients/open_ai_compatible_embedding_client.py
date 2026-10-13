"""Embeddings through any OpenAI-compatible endpoint (Jina AI by default)."""

from openai import APIError, AsyncOpenAI

from app.clients.embedding_client import EmbeddingPurpose
from app.core.exceptions import ProviderError
from app.core.logging import get_logger

_logger = get_logger("embeddings")


class OpenAiCompatibleEmbeddingClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        dimensions: int,
        batch_size: int,
        passage_task: str = "",
        query_task: str = "",
    ) -> None:
        self._client = AsyncOpenAI(base_url=base_url, api_key=api_key or "missing-key")
        self._model = model
        self._dimensions = dimensions
        self._batch_size = batch_size
        self._tasks = {"passage": passage_task, "query": query_task}

    async def embed(self, texts: list[str], purpose: EmbeddingPurpose) -> list[list[float]]:
        vectors: list[list[float]] = []
        task = self._tasks[purpose]
        extra_body = {"task": task} if task else None
        for start in range(0, len(texts), self._batch_size):
            batch = texts[start : start + self._batch_size]
            try:
                response = await self._client.embeddings.create(
                    model=self._model,
                    input=batch,
                    dimensions=self._dimensions,
                    encoding_format="float",
                    extra_body=extra_body,
                )
            except APIError as error:
                _logger.warning("Embedding request failed: %s", error)
                raise ProviderError("The embeddings service is not available right now.") from error
            vectors.extend(item.embedding for item in sorted(response.data, key=lambda d: d.index))
            _logger.info("Embedded %d/%d texts", min(start + len(batch), len(texts)), len(texts))
        return vectors
