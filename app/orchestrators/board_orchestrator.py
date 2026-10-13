"""Runs the board agents in order: Extractor per meeting, then Stance, then Timeline.

Agents never call each other; this class passes data between them. No DB access here.
"""

import re
from collections.abc import Awaitable, Callable

from app.agents.extractor_agent import ExtractorAgent
from app.agents.stance_agent import StanceAgent
from app.agents.timeline_agent import TimelineAgent
from app.core.logging import get_logger
from app.schemas.board_build_input import BoardBuildInput, MeetingText
from app.schemas.board_build_output import BoardBuildOutput
from app.schemas.extractor_input import ExtractorInput
from app.schemas.extractor_output import ExtractorOutput
from app.schemas.stance_input import StanceInput
from app.schemas.stance_output import StanceOutput
from app.schemas.timeline_input import TimelineInput
from app.schemas.timeline_output import TimelineOutput

_logger = get_logger("board")
_LINE_TAG = re.compile(r"^\[L")
_MAX_KNOWN_ITEMS = 40
OnExtracted = Callable[[int, ExtractorOutput], Awaitable[None]]


class BoardOrchestrator:
    def __init__(
        self,
        extractor: ExtractorAgent,
        stance: StanceAgent,
        timeline: TimelineAgent,
        window_lines: int,
        stance_max_lines: int,
    ) -> None:
        self._extractor = extractor
        self._stance = stance
        self._timeline = timeline
        self._window_lines = window_lines
        self._stance_max_lines = stance_max_lines

    async def run(
        self, input: BoardBuildInput, on_extracted: OnExtracted | None = None
    ) -> BoardBuildOutput:
        """on_extracted lets the caller save each new extraction at once (no DB access here)."""
        extractions: dict[int, ExtractorOutput] = {}
        new_ids: list[int] = []
        subjects: list[str] = []
        known_items: dict[str, str] = {}
        for meeting in input.meetings:
            output = input.cached.get(meeting.meeting_id)
            if output is None:
                output = await self._extract(meeting, subjects, list(known_items.values()))
                new_ids.append(meeting.meeting_id)
                if on_extracted:
                    await on_extracted(meeting.meeting_id, output)
            extractions[meeting.meeting_id] = output
            subjects = _merge_subjects(subjects, output)
            known_items.update(_known_items(output))

        if not input.meetings:
            return BoardBuildOutput(
                extractions={}, stances=StanceOutput(), timeline=TimelineOutput()
            )
        stances = await self._stance.run(self._stance_input(input.meetings, subjects))
        timeline = await self._run_timeline(input.meetings, extractions)
        return BoardBuildOutput(
            extractions=extractions, new_extraction_ids=new_ids, stances=stances, timeline=timeline
        )

    async def _extract(
        self, meeting: MeetingText, subjects: list[str], known_items: list[str]
    ) -> ExtractorOutput:
        """Long meetings are read in windows so each call stays under the token limit."""
        combined = ExtractorOutput()
        windows = range(0, len(meeting.lines), self._window_lines)
        for index, start in enumerate(windows, start=1):
            _logger.info(
                "Extracting meeting %s, part %d/%d", meeting.meeting_id, index, len(windows)
            )
            part = await self._extractor.run(
                ExtractorInput(
                    meeting_title=meeting.title,
                    meeting_date=meeting.meeting_date,
                    speakers=meeting.speakers,
                    transcript="\n".join(meeting.lines[start : start + self._window_lines]),
                    known_subjects=subjects,
                    known_items=known_items[-_MAX_KNOWN_ITEMS:],
                )
            )
            combined.decisions.extend(part.decisions)
            combined.action_items.extend(part.action_items)
            combined.open_items.extend(part.open_items)
            subjects = _merge_subjects(subjects, part)
        return combined

    def _stance_input(self, meetings: list[MeetingText], subjects: list[str]) -> StanceInput:
        total = sum(len(m.lines) for m in meetings)
        keep_every = max(1, -(-total // self._stance_max_lines))  # ceiling division
        blocks: list[str] = []
        speakers: list[str] = []
        for meeting in meetings:
            header = f"## M{meeting.meeting_id} | {meeting.meeting_date} | {meeting.title}"
            lines = meeting.lines[::keep_every]
            tagged = [_LINE_TAG.sub(f"[M{meeting.meeting_id} L", line, count=1) for line in lines]
            blocks.append("\n".join([header, *tagged]))
            speakers.extend(s for s in meeting.speakers if s not in speakers)
        return StanceInput(speakers=speakers, meetings="\n\n".join(blocks), known_subjects=subjects)

    async def _run_timeline(
        self, meetings: list[MeetingText], extractions: dict[int, ExtractorOutput]
    ) -> TimelineOutput:
        rows: list[str] = []
        for meeting in meetings:
            for d in extractions[meeting.meeting_id].decisions:
                refs = ", ".join(f"M{meeting.meeting_id}:L{line}" for line in d.lines)
                rows.append(
                    f"M{meeting.meeting_id} | {meeting.meeting_date} | subject={d.subject} | "
                    f"{d.summary} | by={d.decided_by} | reason={d.reason} | lines={refs}"
                )
        if not rows:
            return TimelineOutput()
        meeting_rows = [f"M{m.meeting_id} | {m.meeting_date} | {m.title}" for m in meetings]
        return await self._timeline.run(
            TimelineInput(meetings="\n".join(meeting_rows), decisions="\n".join(rows))
        )


def _merge_subjects(subjects: list[str], output: ExtractorOutput) -> list[str]:
    found = [
        item.subject
        for group in (output.decisions, output.action_items, output.open_items)
        for item in group
    ]
    return list(dict.fromkeys([*subjects, *(s.strip().lower() for s in found)]))


def _known_items(output: ExtractorOutput) -> dict[str, str]:
    """Latest state per subject, for example 'ingestion prototype | action | owner=... | ...'."""
    items: dict[str, str] = {}
    for d in output.decisions:
        items[d.subject.strip().lower()] = f"{d.subject} | decision | {d.summary}"
    for a in output.action_items:
        owner = a.owner or "Unassigned"
        due = f" | due {a.due}" if a.due else ""
        items[a.subject.strip().lower()] = f"{a.subject} | action | owner={owner}{due} | {a.task}"
    for o in output.open_items:
        items.setdefault(o.subject.strip().lower(), f"{o.subject} | open | {o.question}")
    return items
