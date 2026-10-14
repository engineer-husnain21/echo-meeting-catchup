from app.schemas.answer_output import AnswerOutput


def test_validate_when_status_written_loosely_normalizes_it() -> None:
    assert AnswerOutput.model_validate({"status": "Not discussed"}).status == "not_discussed"
    assert AnswerOutput.model_validate({"status": "needs clarification"}).status == "clarify"
    assert AnswerOutput.model_validate({"status": None}).status == "answered"


def test_validate_when_citation_is_single_object_wraps_it_in_list() -> None:
    output = AnswerOutput.model_validate({"citations": {"meeting_id": "M2", "line": "L11"}})
    assert [(c.meeting_id, c.line) for c in output.citations] == [(2, 11)]


def test_validate_when_answer_has_extra_spaces_cleans_them() -> None:
    assert AnswerOutput.model_validate({"answer": " Mongo\n DB  "}).answer == "Mongo DB"
