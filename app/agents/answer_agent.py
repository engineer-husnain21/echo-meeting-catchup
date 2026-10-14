"""Answer agent: answers one question from the board and retrieved transcript lines."""

from app.agents.base_agent import BaseAgent
from app.schemas.answer_input import AnswerInput
from app.schemas.answer_output import AnswerOutput


class AnswerAgent(BaseAgent[AnswerInput, AnswerOutput]):
    name = "Answer agent"

    async def run(self, input: AnswerInput) -> AnswerOutput:
        user_text = (
            f"Person asking: {input.user_name or '(name not given)'}\n\n"
            f"Meetings (oldest first):\n{input.meetings}\n\n"
            f"<board>\n{input.board_facts or '(board not built yet)'}\n</board>\n\n"
            f"<excerpts>\n{input.excerpts or '(no matching lines)'}\n</excerpts>\n\n"
            f"<conversation>\n{input.conversation or '(no earlier turns)'}\n</conversation>\n\n"
            f"Question: {input.question}"
        )
        return await self._ask("answer_system", user_text, AnswerOutput)
