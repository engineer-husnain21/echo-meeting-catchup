"""Question endpoint: ask ECHO about a topic and get a cited answer."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.dependencies import get_question_service
from app.schemas.answer_response import AnswerResponse
from app.schemas.ask_question_request import AskQuestionRequest
from app.services.question_service import QuestionService

router = APIRouter(prefix="/api/v1/topics/{topic_id}/questions", tags=["questions"])
QuestionServiceDep = Annotated[QuestionService, Depends(get_question_service)]


@router.post("", response_model=AnswerResponse)
async def ask_question(
    topic_id: int, request: AskQuestionRequest, service: QuestionServiceDep
) -> AnswerResponse:
    return await service.ask(topic_id, request)
