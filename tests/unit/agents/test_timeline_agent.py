from app.agents.timeline_agent import TimelineAgent
from app.core.prompt_loader import PromptLoader
from app.schemas.timeline_input import TimelineInput
from tests.fakes.fake_llm_client import FakeLlmClient


async def test_run_when_llm_replies_returns_changes() -> None:
    reply = {
        "changes": [
            {
                "meeting_id": 3,
                "subject": "database choice",
                "change": "Database switched from PostgreSQL to MongoDB.",
                "reason": "Event schema changes too often.",
                "evidence": [{"meeting_id": 3, "line": 7}],
            }
        ]
    }
    llm = FakeLlmClient([reply])
    output = await TimelineAgent(llm, PromptLoader()).run(
        TimelineInput(meetings="M3 | 2026-10-05 | Data model review", decisions="...")
    )
    assert output.changes[0].reason == "Event schema changes too often."
    assert "<decisions>" in llm.calls[0][1]


async def test_run_when_reply_empty_returns_no_changes() -> None:
    output = await TimelineAgent(FakeLlmClient([{}]), PromptLoader()).run(
        TimelineInput(meetings="", decisions="")
    )
    assert output.changes == []
