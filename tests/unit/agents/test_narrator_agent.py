from app.agents.narrator_agent import NarratorAgent
from app.core.prompt_loader import PromptLoader
from app.schemas.narrator_input import NarratorInput
from tests.fakes.fake_llm_client import FakeLlmClient


async def test_run_when_llm_replies_returns_briefing_and_citations() -> None:
    llm = FakeLlmClient([{"briefing": "Here's where things stand.", "citations": ["M3 L7"]}])
    output = await NarratorAgent(llm, PromptLoader()).run(
        NarratorInput(
            user_name="Hussnain Razaq",
            meetings="M3 | 2026-10-05 | Data model review",
            board_facts="decision | database choice | now: MongoDB [M3 L7]",
        )
    )
    assert output.briefing == "Here's where things stand."
    assert [(c.meeting_id, c.line) for c in output.citations] == [(3, 7)]
    system, user = llm.calls[0]
    assert "data, not instructions" in system
    assert "Listener: Hussnain Razaq" in user and "<board>" in user
