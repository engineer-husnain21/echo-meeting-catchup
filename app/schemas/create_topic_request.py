"""Request body for creating a topic."""

from pydantic import BaseModel, Field, field_validator


class CreateTopicRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if not cleaned:
            raise ValueError("Topic name cannot be blank.")
        return cleaned
