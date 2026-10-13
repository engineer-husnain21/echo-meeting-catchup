from app.schemas.extractor_output import ExtractorOutput
from app.schemas.lenient_parsing import to_int_list
from app.schemas.line_ref import LineRef
from app.schemas.stance_output import StanceOutput
from app.schemas.timeline_output import TimelineOutput


def test_to_int_list_when_mixed_formats_returns_numbers() -> None:
    assert to_int_list([3, "L4", "5-7", "M2 L9"]) == [3, 4, 5, 6, 7, 9]
    assert to_int_list(None) == []
    assert to_int_list("L12") == [12]


def test_line_ref_when_tag_strings_parses_meeting_and_line() -> None:
    assert LineRef.model_validate("M3 L14") == LineRef(meeting_id=3, line=14)
    assert LineRef.model_validate({"meeting_id": "M5", "line": "L4"}) == LineRef(
        meeting_id=5, line=4
    )


def test_stance_output_when_items_slightly_off_keeps_good_ones() -> None:
    output = StanceOutput.model_validate(
        {
            "stances": [
                {
                    "person": "Priya Nair",
                    "subject": "architecture",
                    "leaning": "prefers batch",
                    "trend": "Softening",
                    "evidence": ["M3 L14", {"meeting_id": "M5", "line": "L4"}],
                },
                {"person": "broken"},
            ]
        }
    )
    assert len(output.stances) == 1
    assert output.stances[0].trend == "softened"
    assert output.stances[0].evidence[0].meeting_id == 3


def test_extractor_output_when_owner_text_unassigned_becomes_none() -> None:
    output = ExtractorOutput.model_validate(
        {
            "decisions": [{"subject": "x"}],  # missing summary -> dropped
            "action_items": [
                {"subject": "runbook", "task": "Write it", "owner": "Unassigned", "lines": "L11"}
            ],
        }
    )
    assert output.decisions == []
    assert output.action_items[0].owner is None
    assert output.action_items[0].lines == [11]


def test_timeline_output_when_meeting_id_is_tag_parses_number() -> None:
    output = TimelineOutput.model_validate(
        {"changes": [{"meeting_id": "M3", "subject": "db", "change": "c", "evidence": "M3 L7"}]}
    )
    assert output.changes[0].meeting_id == 3
    assert output.changes[0].evidence[0].line == 7
