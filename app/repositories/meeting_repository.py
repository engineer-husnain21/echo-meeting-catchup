"""Reads and writes meetings and their transcript lines."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.meeting import Meeting
from app.models.meeting_line import MeetingLine
from app.schemas.parsed_transcript import ParsedTranscript


class MeetingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_with_lines(self, topic_id: int, transcript: ParsedTranscript) -> Meeting:
        """Store the meeting and all its lines in one transaction."""
        meeting = Meeting(
            topic_id=topic_id,
            title=transcript.title,
            meeting_date=transcript.meeting_date,
            source_filename=transcript.source_filename,
            file_format=transcript.file_format,
            content_hash=transcript.content_hash,
            line_count=len(transcript.lines),
            duration_seconds=transcript.duration_seconds,
        )
        self._session.add(meeting)
        await self._session.flush()
        self._session.add_all(
            MeetingLine(
                meeting_id=meeting.id,
                line_number=line.line_number,
                speaker=line.speaker,
                start_seconds=line.start_seconds,
                end_seconds=line.end_seconds,
                text=line.text,
            )
            for line in transcript.lines
        )
        await self._session.commit()
        return meeting

    async def get_by_id(self, meeting_id: int) -> Meeting | None:
        return await self._session.get(Meeting, meeting_id)

    async def get_by_hash(self, topic_id: int, content_hash: str) -> Meeting | None:
        result = await self._session.execute(
            select(Meeting).where(
                Meeting.topic_id == topic_id, Meeting.content_hash == content_hash
            )
        )
        return result.scalar_one_or_none()

    async def list_by_topic(self, topic_id: int) -> list[Meeting]:
        """Meetings in time order (oldest first)."""
        result = await self._session.execute(
            select(Meeting)
            .where(Meeting.topic_id == topic_id)
            .order_by(Meeting.meeting_date, Meeting.id)
        )
        return list(result.scalars())

    async def count_by_topic(self, topic_id: int) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(Meeting).where(Meeting.topic_id == topic_id)
        )
        return int(result.scalar_one())

    async def get_lines(self, meeting_id: int) -> list[MeetingLine]:
        result = await self._session.execute(
            select(MeetingLine)
            .where(MeetingLine.meeting_id == meeting_id)
            .order_by(MeetingLine.line_number)
        )
        return list(result.scalars())

    async def list_speakers(self, topic_id: int) -> list[str]:
        """Distinct speakers across all meetings of a topic, alphabetically."""
        result = await self._session.execute(
            select(MeetingLine.speaker)
            .join(Meeting, Meeting.id == MeetingLine.meeting_id)
            .where(Meeting.topic_id == topic_id)
            .distinct()
            .order_by(MeetingLine.speaker)
        )
        return list(result.scalars())
