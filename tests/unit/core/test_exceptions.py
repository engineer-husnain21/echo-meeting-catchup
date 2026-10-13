from app.core.exceptions import DuplicateError, EchoError, NotFoundError, ProviderError


def test_exceptions_when_raised_carry_status_and_code() -> None:
    assert NotFoundError("x").status_code == 404
    assert DuplicateError("x").error_code == "duplicate"
    assert ProviderError("x").status_code == 503
    assert isinstance(NotFoundError("x"), EchoError)
