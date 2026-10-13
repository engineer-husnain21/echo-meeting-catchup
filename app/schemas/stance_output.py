"""Output of the Stance agent. Every stance is an inference backed by quoted lines."""

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.lenient_parsing import keep_valid
from app.schemas.line_ref import LineRef

Trend = Literal["unchanged", "softened", "hardened", "reversed"]


class InferredStance(BaseModel):
    person: str
    subject: str
    leaning: str  # short phrase, for example "still prefers batch processing"
    trend: Trend = "unchanged"
    explanation: str = ""
    evidence: list[LineRef] = Field(default_factory=list)

    @field_validator("trend", mode="before")
    @classmethod
    def normalize_trend(cls, value: Any) -> str:
        text = str(value or "").lower()
        for word, trend in (("soft", "softened"), ("hard", "hardened"), ("rever", "reversed")):
            if word in text:
                return trend
        return "unchanged"

    @field_validator("evidence", mode="before")
    @classmethod
    def evidence_list(cls, value: Any) -> Any:
        return value if isinstance(value, list) else [value] if value else []


class StanceOutput(BaseModel):
    stances: list[InferredStance] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def drop_broken_items(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        return {"stances": keep_valid(value.get("stances"), InferredStance, "stance")}
