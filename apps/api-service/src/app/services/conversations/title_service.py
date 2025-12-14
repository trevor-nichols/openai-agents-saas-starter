"""Internal helper to generate and persist conversation titles."""

from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

from agents import Agent, ModelSettings, Runner
from openai.types.shared.reasoning import Reasoning
from pydantic import BaseModel, Field

from app.services.conversation_service import ConversationService
from app.services.conversations import metadata_stream

logger = logging.getLogger(__name__)


class _TitleOutput(BaseModel):
    title: str = Field(
        ...,
        min_length=1,
        max_length=60,
        description="Short title for the conversation.",
    )


def _default_agent(model: str) -> Agent:
    return Agent(
        name="conversation-title-generator",
        instructions=(
            "You name conversations. Given the first user message, return a concise title.\n"
            "- 3 to 8 words\n"
            "- No quotes or trailing punctuation\n"
            "- Title case is okay; avoid emojis"
        ),
        model=model,
        model_settings=ModelSettings(
            reasoning=Reasoning(effort="minimal"),
            verbosity="low",
            max_tokens=64,
            store=False,
        ),
        output_type=_TitleOutput,
    )


class TitleService:
    """Generates short conversation titles and stores them if absent."""

    def __init__(
        self,
        conversation_service: ConversationService,
        *,
        model: str = "gpt-5-nano",
        timeout_seconds: float = 5.0,
        runner: Callable[[Agent, str], Awaitable[object]] | None = None,
    ) -> None:
        self._conversation_service = conversation_service
        self._timeout_seconds = timeout_seconds
        self._agent = _default_agent(model)
        self._runner = runner or Runner.run

    async def generate_if_absent(
        self,
        *,
        conversation_id: str,
        tenant_id: str,
        first_user_message: str,
    ) -> str | None:
        """Generate and persist a title when none exists. Returns the stored title or None."""

        message = (first_user_message or "").strip()
        if not message:
            return None

        try:
            raw_title = await asyncio.wait_for(
                self._runner(self._agent, message),
                timeout=self._timeout_seconds,
            )
        except TimeoutError:
            logger.warning(
                "title_generation.timeout",
                extra={
                    "conversation_id": conversation_id,
                    "tenant_id": tenant_id,
                },
            )
            return None
        except Exception:
            logger.exception(
                "title_generation.error",
                extra={
                    "conversation_id": conversation_id,
                    "tenant_id": tenant_id,
                },
            )
            return None

        title_text = self._extract_title(raw_title)
        if not title_text:
            return None

        try:
            stored = await self._conversation_service.set_display_name(
                conversation_id,
                tenant_id=tenant_id,
                display_name=title_text,
                generated_at=datetime.now(UTC),
            )
            if stored:
                await metadata_stream.publish(
                    tenant_id=tenant_id,
                    conversation_id=conversation_id,
                    event={
                        "kind": "conversation.title.generated",
                        "conversation_id": conversation_id,
                        "display_name": title_text,
                    },
                )
            return title_text if stored else None
        except Exception:
            logger.exception(
                "title_generation.persist_failed",
                extra={
                    "conversation_id": conversation_id,
                    "tenant_id": tenant_id,
                },
            )
            return None

    @staticmethod
    def _extract_title(result: object) -> str | None:
        """Normalize the runner result into a short title string.

        The title generator uses structured output (`output_type=_TitleOutput`), but
        we keep this extractor defensive so unit tests or alternate runners can
        stub in simpler return types.
        """

        if result is None:
            return None

        final_output = getattr(result, "final_output", None)
        candidate = final_output if final_output is not None else result

        text: str | None = None
        if isinstance(candidate, str):
            text = candidate
        elif isinstance(candidate, dict) and "title" in candidate:
            title_val = candidate.get("title")
            text = str(title_val) if title_val is not None else None
        else:
            title_attr = getattr(candidate, "title", None)
            if isinstance(title_attr, str):
                text = title_attr
            else:
                dump_fn = getattr(candidate, "model_dump", None)
                if callable(dump_fn):
                    dumped = dump_fn()
                    if isinstance(dumped, dict) and "title" in dumped:
                        title_val = dumped.get("title")
                        text = str(title_val) if title_val is not None else None

        if not text and hasattr(result, "response_text"):
            response_text = getattr(result, "response_text", None)
            if isinstance(response_text, str):
                text = response_text

        if not text:
            text = str(candidate)

        if not text:
            return None

        normalized = re.sub(r"[\r\n]+", " ", str(text)).strip()
        normalized = re.sub(r"^(title\\s*:\\s*)", "", normalized, flags=re.IGNORECASE)
        normalized = re.sub(r"^[\"'“”]+|[\"'“”]+$", "", normalized)
        normalized = re.sub(r"[.!?]+$", "", normalized)
        normalized = " ".join(normalized.split())  # collapse whitespace

        if not normalized:
            return None

        if len(normalized) > 60:
            normalized = normalized[:60].rstrip()

        return normalized


__all__ = ["TitleService"]
