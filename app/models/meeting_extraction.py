"""Cached Extractor result per meeting, so old meetings are not sent to the LLM again."""

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class MeetingExtraction(Base):
    __tablename__ = "meeting_extractions"

    meeting_id: Mapped[int] = mapped_column(
        ForeignKey("meetings.id", ondelete="CASCADE"), primary_key=True
    )
    data: Mapped[str] = mapped_column(Text)  # ExtractorOutput as JSON
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
