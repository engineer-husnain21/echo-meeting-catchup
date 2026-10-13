"""Meeting endpoints: upload a transcript, list meetings, open a transcript."""

from typing import Annotated

from fastapi import APIRouter, Depends, UploadFile, status

from app.core.dependencies import get_meeting_service, get_meeting_upload_service
from app.schemas.meeting_response import MeetingResponse
from app.schemas.meeting_transcript_response import MeetingTranscriptResponse
from app.schemas.upload_meeting_response import UploadMeetingResponse
from app.services.meeting_service import MeetingService
from app.services.meeting_upload_service import MeetingUploadService

router = APIRouter(prefix="/api/v1", tags=["meetings"])
UploadServiceDep = Annotated[MeetingUploadService, Depends(get_meeting_upload_service)]
MeetingServiceDep = Annotated[MeetingService, Depends(get_meeting_service)]


@router.post(
    "/topics/{topic_id}/meetings",
    response_model=UploadMeetingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_meeting(
    topic_id: int, file: UploadFile, service: UploadServiceDep
) -> UploadMeetingResponse:
    content = await file.read()
    return await service.upload(topic_id, file.filename or "transcript.txt", content)


@router.get("/topics/{topic_id}/meetings", response_model=list[MeetingResponse])
async def list_meetings(topic_id: int, service: MeetingServiceDep) -> list[MeetingResponse]:
    return await service.list_meetings(topic_id)


@router.get("/topics/{topic_id}/speakers", response_model=list[str])
async def list_speakers(topic_id: int, service: MeetingServiceDep) -> list[str]:
    return await service.list_speakers(topic_id)


@router.get("/meetings/{meeting_id}/transcript", response_model=MeetingTranscriptResponse)
async def get_transcript(meeting_id: int, service: MeetingServiceDep) -> MeetingTranscriptResponse:
    return await service.get_transcript(meeting_id)
