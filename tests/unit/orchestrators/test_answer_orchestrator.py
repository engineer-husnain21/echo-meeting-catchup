from datetime import UTC, date, datetime

from app.agents.answer_agent import AnswerAgent
from app.agents.narrator_agent import NarratorAgent
from app.core.prompt_loader import PromptLoader
from app.orchestrators.answer_orchestrator import AnswerOrchestrator
from app.schemas.answer_build_input import AnswerBuildInput
from app.schemas.board_response import (
    BoardActionItem,
    BoardDecision,
    BoardMeeting,
    BoardResponse,
    DecisionVersion,
    Quote,
)
from app.schemas.chat_turn import ChatTurn
from app.schemas.scored_chunk import ScoredChunk
from app.schemas.transcript_chunk import TranscriptChunk
from tests.fakes.fake_llm_client import FakeLlmClient


def _orchestrator(llm: FakeLlmClient) -> AnswerOrchestrator:
    prompts = PromptLoader()
    return AnswerOrchestrator(AnswerAgent(llm, prompts), NarratorAgent(llm, prompts))


MEETINGS = [
    BoardMeeting(id=1, title="Kickoff", meeting_date=date(2026, 9, 28)),
    BoardMeeting(id=3, title="Data model review", meeting_date=date(2026, 10, 5)),
]


def _chunk(meeting_id: int, first: int, last: int) -> ScoredChunk:
    lines = [f"[L{n} 00:{n:02d}] Maya Chen: line {n}" for n in range(first, last + 1)]
    return ScoredChunk(
        chunk=TranscriptChunk(
            topic_id=1,
            meeting_id=meeting_id,
            meeting_title="x",
            meeting_date=date(2026, 10, 1),
            chunk_index=0,
            first_line=first,
            last_line=last,
            start_seconds=None,
            speakers=["Maya Chen"],
            text="\n".join(lines),
        ),
        score=0.5,
    )


def _quote(meeting_id: int, line: int) -> Quote:
    return Quote(
        meeting_id=meeting_id,
        meeting_title="x",
        meeting_date=date(2026, 10, 5),
        line=line,
        speaker="Maya Chen",
        start_seconds=None,
        text="t",
    )


def _board() -> BoardResponse:
    version = DecisionVersion(
        summary="Use MongoDB.",
        decided_by="Maya Chen",
        reason="Schema changes often.",
        meeting_id=3,
        meeting_date=date(2026, 10, 5),
        quotes=[_quote(3, 7)],
    )
    old = version.model_copy(
        update={"summary": "Use PostgreSQL.", "meeting_id": 1, "quotes": [_quote(1, 15)]}
    )
    return BoardResponse(
        topic_id=1,
        updated_at=datetime.now(UTC),
        meetings=MEETINGS,
        decisions=[BoardDecision(subject="database choice", current=version, history=[old])],
        action_items=[
            BoardActionItem(
                subject="on-call runbook",
                task="Write the runbook.",
                owner=None,
                due=None,
                status="open",
                meeting_id=1,
                meeting_date=date(2026, 9, 28),
                quotes=[_quote(1, 20)],
            )
        ],
    )


async def test_run_when_chunks_overlap_merges_lines_in_time_order() -> None:
    llm = FakeLlmClient([{"status": "answered", "answer": "ok"}])
    result = await _orchestrator(llm).run(
        AnswerBuildInput(
            question="q",
            meetings=MEETINGS,
            chunks=[_chunk(3, 5, 8), _chunk(1, 1, 4), _chunk(1, 3, 6), _chunk(9, 1, 2)],
        )
    )
    user = llm.calls[0][1]
    assert user.count("[M1 L3 ") == 1  # overlap kept once
    assert user.index("## M1") < user.index("## M3")  # oldest meeting first
    assert "[M9 " not in user  # chunk from a meeting outside the topic is ignored
    shown = [(r.meeting_id, r.line) for r in result.shown_lines]
    assert shown[:2] == [(1, 1), (1, 2)] and (3, 8) in shown and len(shown) == 10


async def test_run_when_board_exists_passes_facts_with_history_and_unassigned() -> None:
    llm = FakeLlmClient([{"status": "answered", "answer": "ok"}])
    result = await _orchestrator(llm).run(
        AnswerBuildInput(
            question="who owns it?",
            user_name="Hussnain Razaq",
            history=[ChatTurn(role="user", text="tell me about the runbook")],
            meetings=MEETINGS,
            board=_board(),
        )
    )
    user = llm.calls[0][1]
    assert "now: Use MongoDB. Reason: Schema changes often. (by Maya Chen, 2026-10-05) [M3 L7]" in (
        user
    )
    assert "earlier: Use PostgreSQL. (2026-10-05) [M1 L15]" in user
    assert "owner=Unassigned" in user
    assert "User: tell me about the runbook" in user
    assert {(r.meeting_id, r.line) for r in result.shown_lines} == {(3, 7), (1, 15), (1, 20)}


async def test_brief_when_board_given_sends_facts_and_returns_shown_lines() -> None:
    from app.schemas.briefing_build_input import BriefingBuildInput

    llm = FakeLlmClient([{"briefing": "Here's where things stand.", "citations": ["M3 L7"]}])
    result = await _orchestrator(llm).brief(
        BriefingBuildInput(user_name="Hussnain Razaq", meetings=MEETINGS, board=_board())
    )
    user = llm.calls[0][1]
    assert "Listener: Hussnain Razaq" in user and "owner=Unassigned" in user
    assert "M3 | 2026-10-05 | Data model review" in user
    assert result.output.briefing.startswith("Here's")
    assert {(r.meeting_id, r.line) for r in result.shown_lines} == {(3, 7), (1, 15), (1, 20)}
