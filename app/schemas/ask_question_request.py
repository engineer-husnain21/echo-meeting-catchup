"""A question about one topic, with the recent conversation for follow-ups."""

from pydantic import BaseModel, Field, field_validator

from app.schemas.chat_turn import ChatTurn


class AskQuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    history: list[ChatTurn] = Field(default_factory=list, max_length=20)  # oldest first
    user_name: str | None = Field(default=None, max_length=120)  # resolves "I", "me", "my"

    @field_validator("question")
    @classmethod
    def not_blank(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if not cleaned:
            raise ValueError("The question is empty.")
        return cleaned
