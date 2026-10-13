"""Deterministic fake embeddings: similar words give similar vectors. No network."""

import hashlib
import math

from app.clients.embedding_client import EmbeddingPurpose
from app.core.exceptions import ProviderError


class FakeEmbeddingClient:
    def __init__(self, dimensions: int = 768, fail: bool = False) -> None:
        self.dimensions = dimensions
        self.fail = fail
        self.calls: list[tuple[int, EmbeddingPurpose]] = []

    async def embed(self, texts: list[str], purpose: EmbeddingPurpose) -> list[list[float]]:
        self.calls.append((len(texts), purpose))
        if self.fail:
            raise ProviderError("The embeddings service is not available right now.")
        return [self._vector(text) for text in texts]

    def _vector(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for word in text.lower().split():
            digest = hashlib.md5(word.strip(".,:?!").encode()).digest()
            vector[int.from_bytes(digest[:4], "little") % self.dimensions] += 1.0
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]
