"""Turns line pointers from an agent into exact quotes copied from the stored transcript.

Grounding rule: a citation is kept only if the agent was shown that line and the line exists.
"""

from app.models.meeting import Meeting
from app.repositories.meeting_repository import MeetingRepository
from app.schemas.board_response import Quote
from app.schemas.line_ref import LineRef

MAX_CITATIONS = 5


class CitationService:
    def __init__(self, meetings: MeetingRepository) -> None:
        self._meetings = meetings

    async def quotes(
        self,
        citations: list[LineRef],
        shown: list[LineRef],
        meetings: list[Meeting],
        limit: int = MAX_CITATIONS,
    ) -> list[Quote]:
        allowed = {(r.meeting_id, r.line) for r in shown}
        by_id = {m.id: m for m in meetings}
        wanted = list(
            dict.fromkeys(
                (c.meeting_id, c.line)
                for c in citations
                if (c.meeting_id, c.line) in allowed and c.meeting_id in by_id
            )
        )[:limit]
        loaded: dict[int, dict[int, Quote]] = {}
        quotes: list[Quote] = []
        for meeting_id, line in wanted:
            if meeting_id not in loaded:
                loaded[meeting_id] = await self._load(by_id[meeting_id])
            quote = loaded[meeting_id].get(line)
            if quote:
                quotes.append(quote)
        return quotes

    async def _load(self, meeting: Meeting) -> dict[int, Quote]:
        return {
            row.line_number: Quote(
                meeting_id=meeting.id,
                meeting_title=meeting.title,
                meeting_date=meeting.meeting_date,
                line=row.line_number,
                speaker=row.speaker,
                start_seconds=row.start_seconds,
                text=row.text,
            )
            for row in await self._meetings.get_lines(meeting.id)
        }
