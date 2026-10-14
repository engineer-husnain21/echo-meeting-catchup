from sqlalchemy.ext.asyncio import AsyncSession

from app.parsers.vtt_transcript_parser import VttTranscriptParser
from app.repositories.meeting_repository import MeetingRepository
from app.repositories.topic_repository import TopicRepository
from app.schemas.line_ref import LineRef
from app.services.citation_service import CitationService
from app.services.transcript_parsing_service import TranscriptParsingService
from tests.sample_data import ATLAS_DIR

KICKOFF = ATLAS_DIR / "2026-09-28_kickoff.vtt"


def _ref(meeting_id: int, line: int) -> LineRef:
    return LineRef(meeting_id=meeting_id, line=line)


async def test_quotes_when_citations_mixed_keeps_shown_existing_unique_lines(
    db_session: AsyncSession,
) -> None:
    topic = await TopicRepository(db_session).create("Atlas")
    transcript = TranscriptParsingService([VttTranscriptParser()], 10**6).parse(
        KICKOFF.name, KICKOFF.read_bytes()
    )
    repo = MeetingRepository(db_session)
    meeting = await repo.add_with_lines(topic.id, transcript)
    m = meeting.id
    shown = [_ref(m, 15), _ref(m, 18), _ref(m, 99)]
    citations = [_ref(m, 15), _ref(m, 15), _ref(m, 3), _ref(m, 99), _ref(m, 18), _ref(7, 1)]

    quotes = await CitationService(repo).quotes(citations, shown, [meeting])

    # duplicate dropped, L3 not shown, L99 does not exist, meeting 7 is not in the topic
    assert [q.line for q in quotes] == [15, 18]
    assert quotes[0].speaker == "Maya Chen" and "PostgreSQL" in quotes[0].text
    assert await CitationService(repo).quotes(citations, shown, [meeting], limit=1) == quotes[:1]
