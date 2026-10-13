from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.dependencies import get_topic_service
from app.routers import topic_router
from app.schemas.topic_response import TopicResponse


class FakeTopicService:
    async def create_topic(self, name: str) -> TopicResponse:
        return TopicResponse(id=1, name=name, created_at=datetime.now(UTC), meeting_count=0)

    async def list_topics(self) -> list[TopicResponse]:
        return []


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(topic_router.router)
    app.dependency_overrides[get_topic_service] = FakeTopicService
    return TestClient(app)


def test_create_topic_when_valid_returns_201() -> None:
    response = _client().post("/api/v1/topics", json={"name": "  Project   Atlas "})
    assert response.status_code == 201
    assert response.json()["name"] == "Project Atlas"


def test_create_topic_when_blank_name_returns_422() -> None:
    assert _client().post("/api/v1/topics", json={"name": "   "}).status_code == 422
