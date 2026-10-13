"""Base class for every agent: one focused AI task, Pydantic input and output."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel, ValidationError

from app.clients.llm_client import LlmClient
from app.core.exceptions import ProviderError
from app.core.logging import get_logger
from app.core.prompt_loader import PromptLoader

TInput = TypeVar("TInput", bound=BaseModel)
TOutput = TypeVar("TOutput", bound=BaseModel)
TModel = TypeVar("TModel", bound=BaseModel)

_logger = get_logger("agents")


class BaseAgent(ABC, Generic[TInput, TOutput]):  # noqa: UP046  (style from the team guide)
    name: str

    def __init__(self, llm_client: LlmClient, prompt_loader: PromptLoader) -> None:
        self._llm_client = llm_client
        self._prompt_loader = prompt_loader

    @abstractmethod
    async def run(self, input: TInput) -> TOutput: ...

    async def _ask(self, prompt_name: str, user_text: str, output_model: type[TModel]) -> TModel:
        """Call the LLM with a prompt file and validate the JSON reply against output_model."""
        system = self._prompt_loader.load(prompt_name)
        reply = await self._llm_client.complete_json(system, user_text)
        try:
            return output_model.model_validate(reply)
        except ValidationError as error:
            _logger.warning("%s returned an invalid shape: %s", self.name, error)
            raise ProviderError(f"The {self.name} returned an unexpected answer.") from error
