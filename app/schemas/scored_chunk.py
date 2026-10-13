"""A search hit from the vector store."""

from pydantic import BaseModel

from app.schemas.transcript_chunk import TranscriptChunk


class ScoredChunk(BaseModel):
    chunk: TranscriptChunk
    score: float
