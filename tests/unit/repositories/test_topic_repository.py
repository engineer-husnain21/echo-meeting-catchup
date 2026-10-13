from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.topic_repository import TopicRepository


async def test_create_when_called_stores_topic(db_session: AsyncSession) -> None:
    repo = TopicRepository(db_session)
    topic = await repo.create("Project Atlas")
    assert topic.id
    assert (await repo.get_by_name("Project Atlas")) is not None
    assert (await repo.get_by_id(topic.id)) is not None
    assert [t.name for t in await repo.list_all()] == ["Project Atlas"]


async def test_get_by_id_when_missing_returns_none(db_session: AsyncSession) -> None:
    assert await TopicRepository(db_session).get_by_id(999) is None
