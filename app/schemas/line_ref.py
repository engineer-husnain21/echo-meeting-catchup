"""A pointer to one transcript line inside a topic: meeting id + line number."""

import re
from typing import Any

from pydantic import BaseModel, model_validator

_TAG = re.compile(r"M\s*(\d+)\D+?(\d+)")


class LineRef(BaseModel):
    meeting_id: int
    line: int

    @model_validator(mode="before")
    @classmethod
    def accept_tags(cls, value: Any) -> Any:
        """Accept "M3 L12", "M3:L12" or {"meeting_id": "M3", "line": "L12"}."""
        if isinstance(value, str):
            match = _TAG.search(value)
            return {"meeting_id": match[1], "line": match[2]} if match else value
        if isinstance(value, dict):
            cleaned = dict(value)
            for key in ("meeting_id", "line"):
                raw = cleaned.get(key)
                if isinstance(raw, str):
                    digits = re.findall(r"\d+", raw)
                    cleaned[key] = int(digits[-1]) if digits else raw
            return cleaned
        return value
