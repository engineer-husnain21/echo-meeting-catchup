"""Upload flow: validate, parse, store, chunk, embed and index one transcript."""

from app.clients.embedding_client import EmbeddingClient
from app.core.exceptions import DuplicateError, NotFoundError, ProviderError
from app.core.logging import get_logger
from app.repositories.chunk_vector_repository import ChunkVectorRepository
from app.repositories.meeting_repository import MeetingRepository
from app.repositories.topic_repository import TopicRepository
from app.schemas.meeting_response import MeetingResponse
from app.schemas.upload_meeting_response import UploadMeetingResponse
from app.services.transcript_chunking_service import TranscriptChunkingService
from app.services.transcript_parsing_service import TranscriptParsingService

_logger = get_logger("upload")


class MeetingUploadService:
    def __init__(
        self,
        topics: TopicRepository,
        meetings: MeetingRepository,
        parser: TranscriptParsingService,
        chunker: TranscriptChunkingService,
        embeddings: EmbeddingClient,
        vectors: ChunkVectorRepository,
    ) -> None:
        self._topics = topics
        self._meetings = meetings
        self._parser = parser
        self._chunker = chunker
        self._embeddings = embeddings
        self._vectors = vectors

    async def upload(self, topic_id: int, filename: str, content: bytes) -> UploadMeetingResponse:
        if await self._topics.get_by_id(topic_id) is None:
            raise NotFoundError(f"Topic {topic_id} was not found.")

        transcript = self._parser.parse(filename, content)
        existing = await self._meetings.get_by_hash(topic_id, transcript.content_hash)
        if existing:
            raise DuplicateError(
                f"This transcript was already uploaded as '{existing.source_filename}'. "
                "It was not added again."
            )

        meeting = await self._meetings.add_with_lines(topic_id, transcript)
        lines = await self._meetings.get_lines(meeting.id)
        chunks = self._chunker.chunk(meeting, lines)
        _logger.info("Meeting %s: %d lines -> %d chunks", meeting.id, len(lines), len(chunks))

        try:
            vectors = await self._embeddings.embed([c.text for c in chunks], purpose="passage")
            await self._vectors.upsert(chunks, vectors)
        except ProviderError:
            # Undo, so a retry is not reported as a duplicate and the topic stays consistent.
            await self._vectors.delete_meeting(meeting.id)
            await self._meetings.delete(meeting.id)
            raise

        return UploadMeetingResponse(
            meeting=MeetingResponse.model_validate(meeting),
            chunk_count=len(chunks),
            speakers=transcript.speakers,
        )
