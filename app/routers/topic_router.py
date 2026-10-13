"""Topic endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_topic_service
from app.schemas.create_topic_request import CreateTopicRequest
from app.schemas.topic_response import TopicResponse
from app.services.topic_service import TopicService

router = APIRouter(prefix="/api/v1/topics", tags=["topics"])
TopicServiceDep = Annotated[TopicService, Depends(get_topic_service)]


@router.post("", response_model=TopicResponse, status_code=status.HTTP_201_CREATED)
async def create_topic(request: CreateTopicRequest, service: TopicServiceDep) -> TopicResponse:
    return await service.create_topic(request.name)


@router.get("", response_model=list[TopicResponse])
async def list_topics(service: TopicServiceDep) -> list[TopicResponse]:
    return await service.list_topics()


@router.get("/{topic_id}", response_model=TopicResponse)
async def get_topic(topic_id: int, service: TopicServiceDep) -> TopicResponse:
    return await service.get_topic(topic_id)
