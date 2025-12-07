"""Internal helper to generate and persist conversation titles."""

from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

from agents import Agent, Runner
from agents.model_settings import ModelSettings

from app.services.conversation_service import ConversationService
from app.services.conversations import metadata_stream

logger = logging.getLogger(__name__)


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
            temperature=0.2,
        ),
    )


class TitleService:
    """Generates short conversation titles and stores them if absent."""

    def __init__(
        self,
        conversation_service: ConversationService,
        *,
        model: str = "gpt-5-mini",
        timeout_seconds: float = 2.0,
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

        title_text = self._extract_text(raw_title)
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
    def _extract_text(result: object) -> str | None:
        """Normalize the runner result into a short title."""

        if result is None:
            return None

        if hasattr(result, "final_output"):
            text = getattr(result, "final_output", None) or getattr(result, "response_text", None)
        else:
            text = str(result)

        if not text:
            return None

        normalized = re.sub(r"[\r\n]+", " ", str(text)).strip()
        normalized = re.sub(r"^[\"'“”]+|[\"'“”]+$", "", normalized)
        normalized = re.sub(r"[.!?]+$", "", normalized)
        normalized = " ".join(normalized.split())  # collapse whitespace

        if not normalized:
            return None

        if len(normalized) > 60:
            normalized = normalized[:60].rstrip()

        return normalized


__all__ = ["TitleService"]
