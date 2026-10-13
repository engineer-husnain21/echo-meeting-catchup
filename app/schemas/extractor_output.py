"""Output of the Extractor agent. Line numbers point into the meeting that was given."""

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.lenient_parsing import keep_valid, to_int_list


class _Cited(BaseModel):
    subject: str
    lines: list[int] = Field(default_factory=list)

    @field_validator("lines", mode="before")
    @classmethod
    def parse_lines(cls, value: Any) -> list[int]:
        return to_int_list(value)


class ExtractedDecision(_Cited):
    summary: str
    decided_by: str | None = None
    reason: str | None = None


class ExtractedActionItem(_Cited):
    task: str
    owner: str | None = None  # None means nobody took it ("Unassigned")
    due: str | None = None
    status: Literal["open", "done"] = "open"

    @field_validator("owner", mode="before")
    @classmethod
    def blank_owner_is_none(cls, value: Any) -> Any:
        if isinstance(value, str) and value.strip().lower() in {"", "none", "null", "unassigned"}:
            return None
        return value

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value: Any) -> str:
        return "done" if str(value).strip().lower() in {"done", "completed", "complete"} else "open"


class ExtractedOpenItem(_Cited):
    question: str


class ExtractorOutput(BaseModel):
    decisions: list[ExtractedDecision] = Field(default_factory=list)
    action_items: list[ExtractedActionItem] = Field(default_factory=list)
    open_items: list[ExtractedOpenItem] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def drop_broken_items(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        return {
            "decisions": keep_valid(value.get("decisions"), ExtractedDecision, "decision"),
            "action_items": keep_valid(value.get("action_items"), ExtractedActionItem, "action"),
            "open_items": keep_valid(value.get("open_items"), ExtractedOpenItem, "open item"),
        }
