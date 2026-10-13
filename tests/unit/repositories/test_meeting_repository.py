from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.meeting_repository import MeetingRepository
from app.repositories.topic_repository import TopicRepository
from app.schemas.parsed_transcript import ParsedTranscript
from app.schemas.transcript_line import TranscriptLine


def _transcript(day: int, content_hash: str) -> ParsedTranscript:
    return ParsedTranscript(
        source_filename=f"2026-10-0{day}_sync.txt",
        file_format="txt",
        title="Sync",
        meeting_date=date(2026, 10, day),
        content_hash=content_hash,
        lines=[
            TranscriptLine(line_number=1, speaker="Maya Chen", start_seconds=1, text="Hi."),
            TranscriptLine(line_number=2, speaker="Omar Haddad", start_seconds=5, text="Hello."),
        ],
    )


async def test_add_with_lines_when_called_stores_meeting_and_lines(
    db_session: AsyncSession,
) -> None:
    topic = await TopicRepository(db_session).create("Atlas")
    repo = MeetingRepository(db_session)
    meeting = await repo.add_with_lines(topic.id, _transcript(5, "h1"))
    lines = await repo.get_lines(meeting.id)
    assert meeting.line_count == 2
    assert [line.speaker for line in lines] == ["Maya Chen", "Omar Haddad"]
    assert await repo.get_by_hash(topic.id, "h1") is not None
    assert await repo.count_by_topic(topic.id) == 1


async def test_list_by_topic_when_uploaded_out_of_order_returns_oldest_first(
    db_session: AsyncSession,
) -> None:
    topic = await TopicRepository(db_session).create("Atlas")
    repo = MeetingRepository(db_session)
    await repo.add_with_lines(topic.id, _transcript(9, "late"))
    await repo.add_with_lines(topic.id, _transcript(1, "early"))
    meetings = await repo.list_by_topic(topic.id)
    assert [m.content_hash for m in meetings] == ["early", "late"]
    assert await repo.list_speakers(topic.id) == ["Maya Chen", "Omar Haddad"]
