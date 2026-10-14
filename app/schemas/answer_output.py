"""Output of the Answer agent. Citations are line pointers; code fills in the quotes."""

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.lenient_parsing import keep_valid
from app.schemas.line_ref import LineRef

AnswerStatus = Literal["answered", "not_discussed", "clarify"]


class AnswerOutput(BaseModel):
    status: AnswerStatus = "answered"
    answer: str = ""
    citations: list[LineRef] = Field(default_factory=list)

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value: Any) -> str:
        text = str(value or "").lower()
        if "clarif" in text:
            return "clarify"
        if "not" in text or "discuss" in text:
            return "not_discussed"
        return "answered"

    @field_validator("answer", mode="before")
    @classmethod
    def answer_text(cls, value: Any) -> str:
        return " ".join(str(value or "").split())

    @model_validator(mode="before")
    @classmethod
    def drop_broken_citations(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        cleaned = dict(value)
        raw = cleaned.get("citations")
        items = raw if isinstance(raw, list) else [raw] if raw else []
        cleaned["citations"] = keep_valid(items, LineRef, "citation")
        return cleaned
