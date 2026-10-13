"""Response shape for the health endpoint."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Simple liveness information."""

    status: str
    app_name: str
