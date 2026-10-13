"""The latest catch-up board of a topic, stored as JSON."""

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class BoardSnapshot(Base):
    __tablename__ = "board_snapshots"

    topic_id: Mapped[int] = mapped_column(
        ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True
    )
    data: Mapped[str] = mapped_column(Text)  # BoardResponse as JSON
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
