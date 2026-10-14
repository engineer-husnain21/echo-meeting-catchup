"""Output of the Narrator agent: a spoken briefing and the board lines behind it."""

from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.schemas.lenient_parsing import keep_valid
from app.schemas.line_ref import LineRef


class NarratorOutput(BaseModel):
    briefing: str = ""
    citations: list[LineRef] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def lenient(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        text = value.get("briefing") or value.get("script") or value.get("text") or ""
        raw = value.get("citations")
        items = raw if isinstance(raw, list) else [raw] if raw else []
        return {
            "briefing": " ".join(str(text).split()),
            "citations": keep_valid(items, LineRef, "citation"),
        }
