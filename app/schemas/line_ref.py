"""A pointer to one transcript line inside a topic: meeting id + line number."""

from pydantic import BaseModel


class LineRef(BaseModel):
    meeting_id: int
    line: int
