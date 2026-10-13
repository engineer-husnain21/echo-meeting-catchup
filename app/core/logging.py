"""Shared logger setup. Use get_logger() everywhere instead of print()."""

import logging

_LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
_ROOT_LOGGER_NAME = "echo"


def configure_logging(level: str) -> None:
    """Configure the root ECHO logger once at startup."""
    logger = logging.getLogger(_ROOT_LOGGER_NAME)
    logger.setLevel(level.upper())
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(_LOG_FORMAT))
        logger.addHandler(handler)
    logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Return a child logger of the shared ECHO logger."""
    return logging.getLogger(f"{_ROOT_LOGGER_NAME}.{name}")
