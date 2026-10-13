"""Timeline agent: what changed across meetings and why."""

from app.agents.base_agent import BaseAgent
from app.schemas.timeline_input import TimelineInput
from app.schemas.timeline_output import TimelineOutput


class TimelineAgent(BaseAgent[TimelineInput, TimelineOutput]):
    name = "Timeline agent"

    async def run(self, input: TimelineInput) -> TimelineOutput:
        user_text = (
            f"<meetings>\n{input.meetings}\n</meetings>\n\n"
            f"<decisions>\n{input.decisions}\n</decisions>"
        )
        return await self._ask("timeline_system", user_text, TimelineOutput)
