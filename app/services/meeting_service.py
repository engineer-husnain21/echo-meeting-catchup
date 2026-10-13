"""Read-only meeting views: list, transcript and speakers."""

from app.core.exceptions import NotFoundError
from app.repositories.meeting_repository import MeetingRepository
from app.repositories.topic_repository import TopicRepository
from app.schemas.meeting_line_response import MeetingLineResponse
from app.schemas.meeting_response import MeetingResponse
from app.schemas.meeting_transcript_response import MeetingTranscriptResponse


class MeetingService:
    def __init__(self, topics: TopicRepository, meetings: MeetingRepository) -> None:
        self._topics = topics
        self._meetings = meetings

    async def list_meetings(self, topic_id: int) -> list[MeetingResponse]:
        await self._require_topic(topic_id)
        meetings = await self._meetings.list_by_topic(topic_id)
        return [MeetingResponse.model_validate(m) for m in meetings]

    async def list_speakers(self, topic_id: int) -> list[str]:
        await self._require_topic(topic_id)
        return await self._meetings.list_speakers(topic_id)

    async def get_transcript(self, meeting_id: int) -> MeetingTranscriptResponse:
        meeting = await self._meetings.get_by_id(meeting_id)
        if meeting is None:
            raise NotFoundError(f"Meeting {meeting_id} was not found.")
        lines = await self._meetings.get_lines(meeting_id)
        return MeetingTranscriptResponse(
            meeting=MeetingResponse.model_validate(meeting),
            lines=[MeetingLineResponse.model_validate(line) for line in lines],
        )

    async def _require_topic(self, topic_id: int) -> None:
        if await self._topics.get_by_id(topic_id) is None:
            raise NotFoundError(f"Topic {topic_id} was not found.")
