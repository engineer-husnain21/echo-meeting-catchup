"""Extractor agent: decisions, action items and open items of one meeting."""

from app.agents.base_agent import BaseAgent
from app.schemas.extractor_input import ExtractorInput
from app.schemas.extractor_output import ExtractorOutput


class ExtractorAgent(BaseAgent[ExtractorInput, ExtractorOutput]):
    name = "Extractor agent"

    async def run(self, input: ExtractorInput) -> ExtractorOutput:
        known = ", ".join(input.known_subjects) or "(none yet)"
        user_text = (
            f"Meeting: {input.meeting_title} on {input.meeting_date.isoformat()}\n"
            f"Speakers: {', '.join(input.speakers)}\n"
            f"Known subjects: {known}\n\n"
            f"<transcript>\n{input.transcript}\n</transcript>"
        )
        return await self._ask("extractor_system", user_text, ExtractorOutput)
