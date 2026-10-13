import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DuplicateError, NotFoundError
from app.repositories.meeting_repository import MeetingRepository
from app.repositories.topic_repository import TopicRepository
from app.services.topic_service import TopicService


def _service(session: AsyncSession) -> TopicService:
    return TopicService(TopicRepository(session), MeetingRepository(session))


async def test_create_topic_when_new_returns_topic_with_zero_meetings(
    db_session: AsyncSession,
) -> None:
    topic = await _service(db_session).create_topic("Project Atlas")
    assert topic.name == "Project Atlas"
    assert topic.meeting_count == 0


async def test_create_topic_when_name_exists_raises_duplicate(db_session: AsyncSession) -> None:
    service = _service(db_session)
    await service.create_topic("Project Atlas")
    with pytest.raises(DuplicateError):
        await service.create_topic("Project Atlas")


async def test_get_topic_when_missing_raises_not_found(db_session: AsyncSession) -> None:
    with pytest.raises(NotFoundError):
        await _service(db_session).get_topic(42)
