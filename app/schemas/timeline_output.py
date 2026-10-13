"""Output of the Timeline agent: what changed across meetings and why."""

import re
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.lenient_parsing import keep_valid
from app.schemas.line_ref import LineRef


class TimelineChange(BaseModel):
    meeting_id: int
    subject: str
    change: str
    reason: str | None = None
    evidence: list[LineRef] = Field(default_factory=list)

    @field_validator("meeting_id", mode="before")
    @classmethod
    def meeting_number(cls, value: Any) -> Any:
        if isinstance(value, str):
            digits = re.findall(r"\d+", value)
            return int(digits[0]) if digits else value
        return value

    @field_validator("evidence", mode="before")
    @classmethod
    def evidence_list(cls, value: Any) -> Any:
        return value if isinstance(value, list) else [value] if value else []


class TimelineOutput(BaseModel):
    changes: list[TimelineChange] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def drop_broken_items(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        return {"changes": keep_valid(value.get("changes"), TimelineChange, "timeline change")}
