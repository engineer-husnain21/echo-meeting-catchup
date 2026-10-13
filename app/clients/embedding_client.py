"""Interface for any embeddings provider."""

from typing import Literal, Protocol

EmbeddingPurpose = Literal["passage", "query"]


class EmbeddingClient(Protocol):
    """Turns texts into vectors. 'passage' for stored chunks, 'query' for questions."""

    async def embed(self, texts: list[str], purpose: EmbeddingPurpose) -> list[list[float]]: ...
