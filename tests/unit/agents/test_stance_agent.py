from app.agents.stance_agent import StanceAgent
from app.core.prompt_loader import PromptLoader
from app.schemas.stance_input import StanceInput
from tests.fakes.fake_llm_client import FakeLlmClient


async def test_run_when_llm_replies_returns_stances_with_evidence() -> None:
    reply = {
        "stances": [
            {
                "person": "Priya Nair",
                "subject": "architecture approach",
                "leaning": "still prefers batch",
                "trend": "softened",
                "explanation": "She seems to accept it but keeps a fallback.",
                "evidence": [{"meeting_id": 3, "line": 14}, {"meeting_id": 5, "line": 4}],
            }
        ]
    }
    llm = FakeLlmClient([reply])
    agent = StanceAgent(llm, PromptLoader())
    output = await agent.run(
        StanceInput(speakers=["Priya Nair"], meetings="[M3 L14] Priya Nair: hmm", known_subjects=[])
    )
    assert output.stances[0].trend == "softened"
    assert output.stances[0].evidence[1].meeting_id == 5
    assert "<meetings>" in llm.calls[0][1]
