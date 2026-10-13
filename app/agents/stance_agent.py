"""Stance agent: hidden leanings and their shifts across all meetings of a topic."""

from app.agents.base_agent import BaseAgent
from app.schemas.stance_input import StanceInput
from app.schemas.stance_output import StanceOutput


class StanceAgent(BaseAgent[StanceInput, StanceOutput]):
    name = "Stance agent"

    async def run(self, input: StanceInput) -> StanceOutput:
        known = ", ".join(input.known_subjects) or "(none yet)"
        user_text = (
            f"Speakers: {', '.join(input.speakers)}\n"
            f"Known subjects: {known}\n\n"
            f"<meetings>\n{input.meetings}\n</meetings>"
        )
        return await self._ask("stance_system", user_text, StanceOutput)
