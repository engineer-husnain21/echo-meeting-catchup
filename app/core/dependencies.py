"""Dependency wiring for FastAPI Depends. Concrete classes are created only here."""

from app.core.config import Settings, get_settings


def get_app_settings() -> Settings:
    """Provide settings to routers and services."""
    return get_settings()
