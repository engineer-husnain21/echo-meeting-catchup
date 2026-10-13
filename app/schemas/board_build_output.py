"""Raw agent results for a board, before quotes are attached."""

from pydantic import BaseModel, Field

from app.schemas.extractor_output import ExtractorOutput
from app.schemas.stance_output import StanceOutput
from app.schemas.timeline_output import TimelineOutput


class BoardBuildOutput(BaseModel):
    extractions: dict[int, ExtractorOutput]
    new_extraction_ids: list[int] = Field(default_factory=list)
    stances: StanceOutput
    timeline: TimelineOutput
