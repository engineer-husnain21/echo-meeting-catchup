"""Custom exceptions. The error handler middleware maps them to HTTP responses."""


class EchoError(Exception):
    """Base class for all ECHO errors."""

    status_code: int = 500
    error_code: str = "internal_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(EchoError):
    """A requested resource does not exist."""

    status_code = 404
    error_code = "not_found"


class ValidationError(EchoError):
    """Input is invalid (for example a wrong file type or an empty transcript)."""

    status_code = 400
    error_code = "validation_error"


class DuplicateError(EchoError):
    """The same item was submitted twice (for example a duplicate transcript)."""

    status_code = 409
    error_code = "duplicate"


class ProviderError(EchoError):
    """An external provider (LLM, speech, embeddings, vector store) failed."""

    status_code = 503
    error_code = "provider_unavailable"
