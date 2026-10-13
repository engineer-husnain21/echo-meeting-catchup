"""Health endpoint used to check that the server is running."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.config import Settings
from app.core.dependencies import get_app_settings
from app.schemas.health_response import HealthResponse

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def get_health(settings: Annotated[Settings, Depends(get_app_settings)]) -> HealthResponse:
    """Return OK when the server is up."""
    return HealthResponse(status="ok", app_name=settings.app_name)
