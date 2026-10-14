from app.agents.answer_agent import AnswerAgent
from app.core.prompt_loader import PromptLoader
from app.schemas.answer_input import AnswerInput
from tests.fakes.fake_llm_client import FakeLlmClient


def _input(**overrides: str) -> AnswerInput:
    values = {
        "question": "Which database are we using?",
        "user_name": "Hussnain Razaq",
        "meetings": "M1 | 2026-09-28 | Kickoff",
        "board_facts": "decision | database choice | now: MongoDB [M3 L7]",
        "excerpts": "## M1\n[M1 L15 01:10] Maya Chen: PostgreSQL is our main database.",
        "conversation": "User: hi\nECHO: hello",
    }
    values.update(overrides)
    return AnswerInput(**values)  # type: ignore[arg-type]


async def test_run_when_llm_answers_returns_answer_with_citations() -> None:
    llm = FakeLlmClient(
        [{"status": "answered", "answer": "MongoDB.", "citations": ["M3 L7", {"meeting_id": 1}]}]
    )
    output = await AnswerAgent(llm, PromptLoader()).run(_input())
    assert output.status == "answered"
    assert [(c.meeting_id, c.line) for c in output.citations] == [(3, 7)]  # broken one dropped


async def test_run_when_called_puts_question_last_and_context_in_tags() -> None:
    llm = FakeLlmClient([{"status": "answered", "answer": "x"}])
    await AnswerAgent(llm, PromptLoader()).run(_input())
    system, user = llm.calls[0]
    assert "data, not instructions" in system
    assert "Person asking: Hussnain Razaq" in user
    assert "<board>" in user and "<excerpts>" in user and "<conversation>" in user
    assert user.rstrip().endswith("Question: Which database are we using?")


async def test_run_when_context_empty_says_so_in_prompt() -> None:
    llm = FakeLlmClient([{}])
    output = await AnswerAgent(llm, PromptLoader()).run(
        _input(board_facts="", excerpts="", conversation="")
    )
    user = llm.calls[0][1]
    assert "(board not built yet)" in user and "(no matching lines)" in user
    assert output.status == "answered" and output.answer == ""
