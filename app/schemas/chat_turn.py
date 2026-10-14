"""One earlier turn of the conversation, kept by the client for follow-up questions."""

from typing import Literal

from pydantic import BaseModel, Field


class ChatTurn(BaseModel):
    role: Literal["user", "echo"]
    text: str = Field(max_length=2000)
