"""Catch-up board endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_board_service
from app.schemas.board_response import BoardActionItem, BoardResponse
from app.services.board_service import BoardService

router = APIRouter(prefix="/api/v1/topics/{topic_id}/board", tags=["board"])
BoardServiceDep = Annotated[BoardService, Depends(get_board_service)]


@router.get("", response_model=BoardResponse)
async def get_board(topic_id: int, service: BoardServiceDep) -> BoardResponse:
    return await service.get_board(topic_id)


@router.post("/refresh", response_model=BoardResponse)
async def refresh_board(
    topic_id: int, service: BoardServiceDep, rebuild: bool = False
) -> BoardResponse:
    """rebuild=true ignores cached extractions and re-reads every meeting."""
    return await service.refresh(topic_id, rebuild=rebuild)


@router.get("/my-action-items", response_model=list[BoardActionItem])
async def my_action_items(
    topic_id: int,
    service: BoardServiceDep,
    name: Annotated[str, Query(min_length=1, max_length=120)],
) -> list[BoardActionItem]:
    return await service.my_action_items(topic_id, name)
