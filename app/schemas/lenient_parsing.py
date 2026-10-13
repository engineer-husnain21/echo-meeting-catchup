"""Helpers that accept small format slips in LLM JSON instead of failing the whole answer."""

import re
from typing import Any

from pydantic import BaseModel, ValidationError

from app.core.logging import get_logger

_logger = get_logger("agents")
_NUMBER = re.compile(r"\d+")


def to_int_list(value: Any) -> list[int]:
    """Accept [12, "L13", "14-15", "M3 L16"] style line lists. Ranges are expanded."""
    if value is None:
        return []
    items = value if isinstance(value, list) else [value]
    numbers: list[int] = []
    for item in items:
        if isinstance(item, int):
            numbers.append(item)
            continue
        text = str(item)
        found = [int(n) for n in _NUMBER.findall(text.split("M")[-1] if "L" in text else text)]
        if len(found) == 2 and "-" in text:
            numbers.extend(range(found[0], found[1] + 1))
        else:
            numbers.extend(found[-1:])
    return numbers


def keep_valid(items: Any, model: type[BaseModel], label: str) -> list[Any]:
    """Drop list items that do not match the model, instead of rejecting the whole reply."""
    if not isinstance(items, list):
        return []
    kept: list[Any] = []
    for item in items:
        try:
            model.model_validate(item)
            kept.append(item)
        except ValidationError as error:
            _logger.warning("Skipped one %s item: %s", label, error.errors()[0].get("msg"))
    return kept
