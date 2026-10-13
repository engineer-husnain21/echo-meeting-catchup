"""Turns raw agent results into the board: merges meetings and attaches exact quotes.

Grounding rule: the LLM only gives line numbers. Quotes are copied from the stored transcript
lines here, and any item whose cited lines do not exist is dropped.
"""

from datetime import UTC, datetime

from app.core.logging import get_logger
from app.models.meeting import Meeting
from app.models.meeting_line import MeetingLine
from app.schemas.board_build_output import BoardBuildOutput
from app.schemas.board_response import (
    BoardActionItem,
    BoardDecision,
    BoardMeeting,
    BoardOpenItem,
    BoardResponse,
    BoardStance,
    BoardTimelineEntry,
    DecisionVersion,
    Quote,
)
from app.schemas.extractor_output import ExtractorOutput
from app.schemas.line_ref import LineRef

_logger = get_logger("board")
MAX_QUOTES = 5
_EMPTY = ExtractorOutput()


class BoardMergeService:
    def __init__(self) -> None:
        self._meetings: dict[int, Meeting] = {}
        self._lines: dict[tuple[int, int], MeetingLine] = {}
        self._dropped = 0

    def build(
        self,
        topic_id: int,
        meetings: list[Meeting],
        lines: list[MeetingLine],
        output: BoardBuildOutput,
    ) -> BoardResponse:
        self._meetings = {m.id: m for m in meetings}
        self._lines = {(line.meeting_id, line.line_number): line for line in lines}
        self._dropped = 0
        ordered = sorted(meetings, key=lambda m: (m.meeting_date, m.id))

        decisions = self._decisions(ordered, output)
        board = BoardResponse(
            topic_id=topic_id,
            updated_at=datetime.now(UTC),
            meetings=[
                BoardMeeting(id=m.id, title=m.title, meeting_date=m.meeting_date) for m in ordered
            ],
            decisions=decisions,
            action_items=self._action_items(ordered, output),
            open_items=self._open_items(ordered, output, decisions),
            stances=self._stances(output),
            timeline=self._timeline(output),
        )
        board.dropped_ungrounded = self._dropped
        if self._dropped:
            _logger.warning("Dropped %d board items without valid source lines", self._dropped)
        return board

    def _quotes(self, refs: list[LineRef]) -> list[Quote]:
        quotes: list[Quote] = []
        for ref in refs:
            line = self._lines.get((ref.meeting_id, ref.line))
            meeting = self._meetings.get(ref.meeting_id)
            if (
                line is None
                or meeting is None
                or any(q.meeting_id == ref.meeting_id and q.line == ref.line for q in quotes)
            ):
                continue
            quotes.append(
                Quote(
                    meeting_id=meeting.id,
                    meeting_title=meeting.title,
                    meeting_date=meeting.meeting_date,
                    line=line.line_number,
                    speaker=line.speaker,
                    start_seconds=line.start_seconds,
                    text=line.text,
                )
            )
        return quotes[:MAX_QUOTES]

    def _local(self, meeting_id: int, lines: list[int]) -> list[Quote]:
        return self._quotes([LineRef(meeting_id=meeting_id, line=n) for n in lines])

    def _decisions(self, ordered: list[Meeting], output: BoardBuildOutput) -> list[BoardDecision]:
        versions: dict[str, list[DecisionVersion]] = {}
        for meeting in ordered:
            for d in output.extractions.get(meeting.id, _EMPTY).decisions:
                quotes = self._local(meeting.id, d.lines)
                if not quotes:
                    self._dropped += 1
                    continue
                versions.setdefault(_key(d.subject), []).append(
                    DecisionVersion(
                        summary=d.summary,
                        decided_by=d.decided_by,
                        reason=d.reason,
                        meeting_id=meeting.id,
                        meeting_date=meeting.meeting_date,
                        quotes=quotes,
                    )
                )
        return [
            BoardDecision(subject=subject, current=items[-1], history=items[:-1])
            for subject, items in versions.items()
        ]

    def _action_items(
        self, ordered: list[Meeting], output: BoardBuildOutput
    ) -> list[BoardActionItem]:
        merged: dict[str, BoardActionItem] = {}
        for meeting in ordered:
            for a in output.extractions.get(meeting.id, _EMPTY).action_items:
                quotes = self._local(meeting.id, a.lines)
                if not quotes:
                    self._dropped += 1
                    continue
                previous = merged.get(_key(a.subject))
                owner = a.owner or (previous.owner if previous else None)
                all_quotes = (previous.quotes if previous else []) + quotes
                merged[_key(a.subject)] = BoardActionItem(
                    subject=_key(a.subject),
                    task=a.task,
                    owner=owner,
                    due=a.due or (previous.due if previous else None),
                    status=a.status,
                    meeting_id=meeting.id,
                    meeting_date=meeting.meeting_date,
                    quotes=all_quotes[-MAX_QUOTES:],
                )
        return list(merged.values())

    def _open_items(
        self, ordered: list[Meeting], output: BoardBuildOutput, decisions: list[BoardDecision]
    ) -> list[BoardOpenItem]:
        decided_on = {d.subject: d.current.meeting_date for d in decisions}
        items: dict[str, BoardOpenItem] = {}
        last_raised: dict[str, Meeting] = {}
        for meeting in ordered:
            for o in output.extractions.get(meeting.id, _EMPTY).open_items:
                quotes = self._local(meeting.id, o.lines)
                if not quotes:
                    self._dropped += 1
                    continue
                key = _key(o.subject)
                last_raised[key] = meeting
                if key in items:
                    items[key].quotes = (items[key].quotes + quotes)[:MAX_QUOTES]
                    continue
                items[key] = BoardOpenItem(
                    subject=key,
                    question=o.question,
                    raised_in_meeting_id=meeting.id,
                    raised_on=meeting.meeting_date,
                    quotes=quotes,
                )
        return [
            item
            for key, item in items.items()
            if key not in decided_on or decided_on[key] < last_raised[key].meeting_date
        ]

    def _stances(self, output: BoardBuildOutput) -> list[BoardStance]:
        stances: list[BoardStance] = []
        for s in output.stances.stances:
            quotes = self._quotes(s.evidence)
            if len(quotes) < 2:  # a hidden stance needs at least two proof lines
                self._dropped += 1
                continue
            stances.append(
                BoardStance(
                    person=s.person,
                    subject=_key(s.subject),
                    leaning=s.leaning,
                    trend=s.trend,
                    explanation=s.explanation,
                    quotes=quotes,
                )
            )
        return stances

    def _timeline(self, output: BoardBuildOutput) -> list[BoardTimelineEntry]:
        entries: list[BoardTimelineEntry] = []
        for c in output.timeline.changes:
            meeting = self._meetings.get(c.meeting_id)
            quotes = self._quotes(c.evidence)
            if meeting is None or not quotes:
                self._dropped += 1
                continue
            entries.append(
                BoardTimelineEntry(
                    meeting_id=meeting.id,
                    meeting_title=meeting.title,
                    meeting_date=meeting.meeting_date,
                    subject=_key(c.subject),
                    change=c.change,
                    reason=c.reason,
                    quotes=quotes,
                )
            )
        return sorted(entries, key=lambda e: (e.meeting_date, e.meeting_id))


def _key(subject: str) -> str:
    return " ".join(subject.lower().split())
