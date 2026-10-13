"""Business rules for topics."""

from app.core.exceptions import DuplicateError, NotFoundError
from app.models.topic import Topic
from app.repositories.meeting_repository import MeetingRepository
from app.repositories.topic_repository import TopicRepository
from app.schemas.topic_response import TopicResponse


class TopicService:
    def __init__(self, topics: TopicRepository, meetings: MeetingRepository) -> None:
        self._topics = topics
        self._meetings = meetings

    async def create_topic(self, name: str) -> TopicResponse:
        if await self._topics.get_by_name(name):
            raise DuplicateError(f"A topic named '{name}' already exists.")
        topic = await self._topics.create(name)
        return await self._to_response(topic)

    async def list_topics(self) -> list[TopicResponse]:
        return [await self._to_response(topic) for topic in await self._topics.list_all()]

    async def get_topic(self, topic_id: int) -> TopicResponse:
        return await self._to_response(await self.require_topic(topic_id))

    async def require_topic(self, topic_id: int) -> Topic:
        topic = await self._topics.get_by_id(topic_id)
        if topic is None:
            raise NotFoundError(f"Topic {topic_id} was not found.")
        return topic

    async def _to_response(self, topic: Topic) -> TopicResponse:
        return TopicResponse(
            id=topic.id,
            name=topic.name,
            created_at=topic.created_at,
            meeting_count=await self._meetings.count_by_topic(topic.id),
        )
