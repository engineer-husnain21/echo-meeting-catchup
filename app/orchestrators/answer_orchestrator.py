"""Prepares the question context and runs the Answer agent.

No DB access here: the service passes in the found chunks and the stored board.
"""

import re

from app.agents.answer_agent import AnswerAgent
from app.schemas.answer_build_input import AnswerBuildInput
from app.schemas.answer_build_output import AnswerBuildOutput
from app.schemas.answer_input import AnswerInput
from app.schemas.board_response import BoardResponse, Quote
from app.schemas.chat_turn import ChatTurn
from app.schemas.line_ref import LineRef
from app.schemas.scored_chunk import ScoredChunk

_LINE_NUMBER = re.compile(r"^\[L(\d+)")
_SPEAKER = {"user": "User", "echo": "ECHO"}


class AnswerOrchestrator:
    def __init__(self, answer: AnswerAgent) -> None:
        self._answer = answer

    async def run(self, input: AnswerBuildInput) -> AnswerBuildOutput:
        order = {m.id: index for index, m in enumerate(input.meetings)}
        excerpts, excerpt_refs = _excerpts(input.chunks, order)
        facts, fact_refs = _board_facts(input.board) if input.board else ("", [])
        output = await self._answer.run(
            AnswerInput(
                question=input.question,
                user_name=input.user_name,
                meetings="\n".join(
                    f"M{m.id} | {m.meeting_date} | {m.title}" for m in input.meetings
                ),
                board_facts=facts,
                excerpts=excerpts,
                conversation=_conversation(input.history),
            )
        )
        shown = list(dict.fromkeys((r.meeting_id, r.line) for r in [*fact_refs, *excerpt_refs]))
        return AnswerBuildOutput(
            output=output, shown_lines=[LineRef(meeting_id=m, line=n) for m, n in shown]
        )


def _excerpts(chunks: list[ScoredChunk], order: dict[int, int]) -> tuple[str, list[LineRef]]:
    """Merge overlapping chunks into one list of tagged lines per meeting, in time order."""
    lines: dict[tuple[int, int], str] = {}
    for scored in chunks:
        meeting_id = scored.chunk.meeting_id
        if meeting_id not in order:
            continue
        for raw in scored.chunk.text.splitlines():
            match = _LINE_NUMBER.match(raw)
            if match:
                lines[(meeting_id, int(match[1]))] = f"[M{meeting_id} L{raw[2:]}"
    keys = sorted(lines, key=lambda key: (order[key[0]], key[1]))
    blocks: list[str] = []
    current: int | None = None
    for meeting_id, line in keys:
        if meeting_id != current:
            blocks.append(f"## M{meeting_id}")
            current = meeting_id
        blocks.append(lines[(meeting_id, line)])
    return "\n".join(blocks), [LineRef(meeting_id=m, line=n) for m, n in keys]


def _board_facts(board: BoardResponse) -> tuple[str, list[LineRef]]:
    rows: list[str] = []
    refs: list[LineRef] = []

    def tags(quotes: list[Quote]) -> str:
        refs.extend(LineRef(meeting_id=q.meeting_id, line=q.line) for q in quotes)
        return " ".join(f"[M{q.meeting_id} L{q.line}]" for q in quotes)

    for d in board.decisions:
        current = d.current
        by = f"by {current.decided_by}, " if current.decided_by else ""
        reason = f" Reason: {current.reason}" if current.reason else ""
        row = (
            f"decision | {d.subject} | now: {current.summary}{reason} "
            f"({by}{current.meeting_date}) {tags(current.quotes)}"
        )
        for old in d.history:
            row += f" | earlier: {old.summary} ({old.meeting_date}) {tags(old.quotes)}"
        rows.append(row)
    for a in board.action_items:
        rows.append(
            f"action | {a.subject} | owner={a.owner or 'Unassigned'} | due={a.due or '-'} | "
            f"status={a.status} | {a.task} {tags(a.quotes)}"
        )
    for o in board.open_items:
        rows.append(f"open | {o.subject} | {o.question} (raised {o.raised_on}) {tags(o.quotes)}")
    for s in board.stances:
        rows.append(
            f"inferred stance | {s.person} | {s.subject} | {s.leaning} ({s.trend}) | "
            f"{s.explanation} {tags(s.quotes)}"
        )
    return "\n".join(rows), refs


def _conversation(history: list[ChatTurn]) -> str:
    return "\n".join(f"{_SPEAKER[turn.role]}: {turn.text}" for turn in history)
