"""Reads and writes topics."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.topic import Topic


class TopicRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, name: str) -> Topic:
        topic = Topic(name=name)
        self._session.add(topic)
        await self._session.commit()
        return topic

    async def get_by_id(self, topic_id: int) -> Topic | None:
        return await self._session.get(Topic, topic_id)

    async def get_by_name(self, name: str) -> Topic | None:
        result = await self._session.execute(select(Topic).where(Topic.name == name))
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Topic]:
        result = await self._session.execute(select(Topic).order_by(Topic.created_at))
        return list(result.scalars())
