"""Stores and searches transcript chunk vectors in Qdrant, one collection for all topics."""

import uuid

from qdrant_client import AsyncQdrantClient, models
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse

from app.core.exceptions import ProviderError
from app.core.logging import get_logger
from app.schemas.scored_chunk import ScoredChunk
from app.schemas.transcript_chunk import TranscriptChunk

_logger = get_logger("vectors")
_POINT_NAMESPACE = uuid.UUID("6f1d2c6e-6b8e-4c39-9a8f-0e5c7d2a9b11")
_QDRANT_ERRORS = (UnexpectedResponse, ResponseHandlingException, ConnectionError, TimeoutError)


class ChunkVectorRepository:
    def __init__(self, client: AsyncQdrantClient, collection: str, dimensions: int) -> None:
        self._client = client
        self._collection = collection
        self._dimensions = dimensions
        self._ready = False

    async def upsert(self, chunks: list[TranscriptChunk], vectors: list[list[float]]) -> None:
        await self._ensure_collection()
        points = [
            models.PointStruct(
                id=str(uuid.uuid5(_POINT_NAMESPACE, f"{c.meeting_id}:{c.chunk_index}")),
                vector=vector,
                payload=c.model_dump(mode="json"),
            )
            for c, vector in zip(chunks, vectors, strict=True)
        ]
        try:
            await self._client.upsert(collection_name=self._collection, points=points, wait=True)
        except _QDRANT_ERRORS as error:
            raise ProviderError("The vector store is not available right now.") from error

    async def search(self, topic_id: int, vector: list[float], limit: int) -> list[ScoredChunk]:
        await self._ensure_collection()
        try:
            result = await self._client.query_points(
                collection_name=self._collection,
                query=vector,
                query_filter=self._match("topic_id", topic_id),
                limit=limit,
                with_payload=True,
            )
        except _QDRANT_ERRORS as error:
            raise ProviderError("The vector store is not available right now.") from error
        return [
            ScoredChunk(chunk=TranscriptChunk.model_validate(point.payload), score=point.score)
            for point in result.points
            if point.payload
        ]

    async def delete_meeting(self, meeting_id: int) -> None:
        await self._ensure_collection()
        try:
            await self._client.delete(
                collection_name=self._collection,
                points_selector=models.FilterSelector(filter=self._match("meeting_id", meeting_id)),
            )
        except _QDRANT_ERRORS as error:
            _logger.warning("Could not delete vectors of meeting %s: %s", meeting_id, error)

    async def _ensure_collection(self) -> None:
        if self._ready:
            return
        try:
            if not await self._client.collection_exists(self._collection):
                await self._client.create_collection(
                    collection_name=self._collection,
                    vectors_config=models.VectorParams(
                        size=self._dimensions, distance=models.Distance.COSINE
                    ),
                )
                for field in ("topic_id", "meeting_id"):
                    await self._client.create_payload_index(
                        collection_name=self._collection,
                        field_name=field,
                        field_schema=models.PayloadSchemaType.INTEGER,
                    )
                _logger.info("Created Qdrant collection %s", self._collection)
        except _QDRANT_ERRORS as error:
            raise ProviderError("The vector store is not available right now.") from error
        self._ready = True

    @staticmethod
    def _match(field: str, value: int) -> models.Filter:
        return models.Filter(
            must=[models.FieldCondition(key=field, match=models.MatchValue(value=value))]
        )
