from datetime import date

from app.agents.extractor_agent import ExtractorAgent
from app.agents.stance_agent import StanceAgent
from app.agents.timeline_agent import TimelineAgent
from app.core.prompt_loader import PromptLoader
from app.orchestrators.board_orchestrator import BoardOrchestrator
from app.schemas.board_build_input import BoardBuildInput, MeetingText
from app.schemas.extractor_output import ExtractorOutput
from tests.fakes.fake_llm_client import FakeLlmClient


def _orchestrator(
    llm: FakeLlmClient, window: int = 150, stance_max: int = 400
) -> BoardOrchestrator:
    prompts = PromptLoader()
    return BoardOrchestrator(
        ExtractorAgent(llm, prompts),
        StanceAgent(llm, prompts),
        TimelineAgent(llm, prompts),
        window_lines=window,
        stance_max_lines=stance_max,
    )


def _meeting(meeting_id: int, line_count: int) -> MeetingText:
    return MeetingText(
        meeting_id=meeting_id,
        title=f"M{meeting_id}",
        meeting_date=date(2026, 10, meeting_id),
        speakers=["Maya Chen"],
        lines=[f"[L{i} 00:0{i % 10}] Maya Chen: line {i}" for i in range(1, line_count + 1)],
    )


async def test_run_when_meeting_cached_skips_extractor() -> None:
    llm = FakeLlmClient(
        [{}, {}]
    )  # extraction of meeting 2, then stance; no decisions -> no timeline
    cached = {1: ExtractorOutput()}
    output = await _orchestrator(llm).run(
        BoardBuildInput(meetings=[_meeting(1, 3), _meeting(2, 3)], cached=cached)
    )
    assert output.new_extraction_ids == [2]
    assert len(llm.calls) == 2
    assert "[M1 L1" in llm.calls[1][1]  # stance input carries meeting tags


async def test_run_when_meeting_is_long_extracts_in_windows() -> None:
    llm = FakeLlmClient()
    output = await _orchestrator(llm, window=10).run(BoardBuildInput(meetings=[_meeting(1, 25)]))
    assert output.new_extraction_ids == [1]
    assert len(llm.calls) == 3 + 1  # three windows + stance


async def test_run_when_many_lines_samples_stance_input() -> None:
    llm = FakeLlmClient()
    await _orchestrator(llm, stance_max=10).run(BoardBuildInput(meetings=[_meeting(1, 40)]))
    assert llm.calls[-1][1].count("Maya Chen: line") == 10


async def test_run_when_no_meetings_calls_nothing() -> None:
    llm = FakeLlmClient()
    output = await _orchestrator(llm).run(BoardBuildInput(meetings=[]))
    assert output.extractions == {} and llm.calls == []
