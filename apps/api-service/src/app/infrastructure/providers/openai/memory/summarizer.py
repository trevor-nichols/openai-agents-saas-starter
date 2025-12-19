from __future__ import annotations

import asyncio
from collections.abc import Callable

from app.core.settings import Settings, get_settings
from openai import AsyncOpenAI

from .strategy import Summarizer


class OpenAISummarizer(Summarizer):
    """Production summarizer using OpenAI GPT models."""

    def __init__(
        self,
        *,
        settings_factory: Callable[[], Settings] = get_settings,
        model: str = "gpt-5.1",
        max_tokens: int = 300,
        max_chars: int = 4000,
        max_retries: int = 2,
        backoff_seconds: float = 0.5,
    ) -> None:
        self._settings_factory = settings_factory
        self._model = model
        self._max_tokens = max_tokens
        self._max_chars = max_chars
        self._max_retries = max_retries
        self._backoff_seconds = backoff_seconds

    async def summarize(self, text: str) -> str:
        settings = self._settings_factory()
        if not settings.openai_api_key:
            return text

        client = AsyncOpenAI(api_key=settings.openai_api_key)
        prompt_text = text if len(text) <= self._max_chars else text[: self._max_chars]
        system_prompt = (
            "You are a concise assistant that summarizes prior conversation context. "
            "Return a faithful, compact summary in plain text. "
            f"Keep within ~{self._max_tokens} tokens and avoid bullets unless necessary."
        )

        last_error: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                response = await client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt_text},
                    ],
                    max_tokens=self._max_tokens,
                    temperature=0.2,
                )
                choice = response.choices[0]
                content = choice.message.content if choice and choice.message else None
                return content or prompt_text
            except Exception as exc:  # pragma: no cover - network/provider failure
                last_error = exc
                if attempt >= self._max_retries:
                    break
                await asyncio.sleep(self._backoff_seconds * (2**attempt))

        return prompt_text if last_error else prompt_text


__all__ = ["OpenAISummarizer"]
