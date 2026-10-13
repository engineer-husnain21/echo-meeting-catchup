"""Chat completions through any OpenAI-compatible endpoint (Groq by default)."""

import json
from typing import Any

from openai import APIError, AsyncOpenAI, RateLimitError

from app.core.exceptions import ProviderError
from app.core.logging import get_logger

_logger = get_logger("llm")
_JSON_ATTEMPTS = 2


class OpenAiCompatibleLlmClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        max_tokens: int,
        timeout_seconds: int,
        reasoning_effort: str = "",
    ) -> None:
        self._client = AsyncOpenAI(
            base_url=base_url, api_key=api_key or "missing-key", timeout=timeout_seconds
        )
        self._model = model
        self._max_tokens = max_tokens
        self._extra_body = {"reasoning_effort": reasoning_effort} if reasoning_effort else None

    async def complete_json(self, system: str, user: str) -> dict[str, Any]:
        for attempt in range(1, _JSON_ATTEMPTS + 1):
            text = await self._complete(system, user)
            try:
                parsed = json.loads(_strip_fences(text))
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass
            _logger.warning("LLM reply was not a JSON object (attempt %d)", attempt)
        raise ProviderError("The language model gave an unreadable answer. Please try again.")

    async def _complete(self, system: str, user: str) -> str:
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                response_format={"type": "json_object"},
                max_tokens=self._max_tokens,
                temperature=0,
                extra_body=self._extra_body,
            )
        except RateLimitError as error:
            _logger.warning("LLM rate limited: %r", error)
            raise ProviderError(
                "The language model is busy (rate limit). Try again soon."
            ) from error
        except APIError as error:
            _logger.warning("LLM request failed: %r", error)
            raise ProviderError("The language model is not available right now.") from error
        usage = response.usage
        if usage:
            _logger.info("LLM tokens: in=%d out=%d", usage.prompt_tokens, usage.completion_tokens)
        return response.choices[0].message.content or ""


def _strip_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.removeprefix("json").strip()
    return cleaned
