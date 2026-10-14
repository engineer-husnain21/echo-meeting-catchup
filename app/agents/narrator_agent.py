"""Narrator agent: turns the catch-up board into a short spoken briefing."""

from app.agents.base_agent import BaseAgent
from app.schemas.narrator_input import NarratorInput
from app.schemas.narrator_output import NarratorOutput


class NarratorAgent(BaseAgent[NarratorInput, NarratorOutput]):
    name = "Narrator agent"

    async def run(self, input: NarratorInput) -> NarratorOutput:
        user_text = (
            f"Listener: {input.user_name or '(name not given)'}\n\n"
            f"Meetings (oldest first):\n{input.meetings}\n\n"
            f"<board>\n{input.board_facts}\n</board>"
        )
        return await self._ask("narrator_system", user_text, NarratorOutput)
