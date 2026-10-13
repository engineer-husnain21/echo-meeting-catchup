"""Output of the Stance agent. Every stance is an inference backed by quoted lines."""

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.line_ref import LineRef


class InferredStance(BaseModel):
    person: str
    subject: str
    leaning: str  # short phrase, for example "still prefers batch processing"
    trend: Literal["unchanged", "softened", "hardened", "reversed"] = "unchanged"
    explanation: str
    evidence: list[LineRef] = Field(default_factory=list)


class StanceOutput(BaseModel):
    stances: list[InferredStance] = Field(default_factory=list)
