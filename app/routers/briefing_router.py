"""Briefing endpoint: a short spoken catch-up of a topic."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.dependencies import get_briefing_service
from app.schemas.briefing_request import BriefingRequest
from app.schemas.briefing_response import BriefingResponse
from app.services.briefing_service import BriefingService

router = APIRouter(prefix="/api/v1/topics/{topic_id}/briefing", tags=["briefing"])
BriefingServiceDep = Annotated[BriefingService, Depends(get_briefing_service)]


@router.post("", response_model=BriefingResponse)
async def create_briefing(
    topic_id: int, request: BriefingRequest, service: BriefingServiceDep
) -> BriefingResponse:
    return await service.brief(topic_id, request.user_name)
