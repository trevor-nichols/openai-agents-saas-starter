"""Internal helper to stream and persist conversation titles.

Design goals:
- The `/api/v1/conversations/{id}/stream` endpoint should stream the *LLM output*
  (ChatGPT-esque "title appears as it is generated"), not app-defined metadata.
- Titles are persisted as `agent_conversations.display_name` once, and are derived
  solely from the first user message of a conversation.
"""

from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import AsyncIterator, Callable
from datetime import UTC, datetime
from typing import Any, Protocol

from agents import Agent, ModelSettings, Runner
from openai.types.shared.reasoning import Reasoning
from pydantic import BaseModel, Field

from app.services.conversation_service import ConversationService

logger = logging.getLogger(__name__)


class _TitleOutput(BaseModel):
    title: str = Field(
        ...,
        min_length=1,
        max_length=60,
        description="Short title for the conversation.",
    )


class _RunnerStream(Protocol):
    """Protocol for streamed Runner results (used for dependency injection + tests)."""

    final_output: Any

    def stream_events(self) -> AsyncIterator[Any]: ...


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


class _JsonStringFieldExtractor:
    """Streaming extractor for a JSON string field value.

    Used to stream *only* the `title` field from a structured-output JSON response
    (i.e. ignore braces, other keys, etc.).
    """

    def __init__(self, field_name: str) -> None:
        self._field_pattern = f"\"{field_name}\""
        self._pattern_index = 0
        self._state: str = "search_key"
        self._escape_pending = False
        self._unicode_pending: list[str] | None = None

    def feed(self, chunk: str) -> str:
        """Consume raw JSON text and return newly extracted characters (may be empty)."""

        if not chunk:
            return ""

        out: list[str] = []
        for ch in chunk:
            emitted = self._feed_char(ch)
            if emitted:
                out.append(emitted)
        return "".join(out)

    def _feed_char(self, ch: str) -> str:
        if self._state == "search_key":
            return self._search_key(ch)
        if self._state == "seek_colon":
            return self._seek_colon(ch)
        if self._state == "seek_value_quote":
            return self._seek_value_quote(ch)
        if self._state == "in_string":
            return self._in_string(ch)
        return ""

    def _search_key(self, ch: str) -> str:
        expected = self._field_pattern[self._pattern_index]
        if ch == expected:
            self._pattern_index += 1
            if self._pattern_index >= len(self._field_pattern):
                self._state = "seek_colon"
                self._pattern_index = 0
            return ""

        # Restart matching if this character could be the beginning of the pattern.
        self._pattern_index = 1 if ch == self._field_pattern[0] else 0
        return ""

    def _seek_colon(self, ch: str) -> str:
        if ch.isspace():
            return ""
        if ch == ":":
            self._state = "seek_value_quote"
            return ""
        # Unexpected token; reset.
        self._state = "search_key"
        return ""

    def _seek_value_quote(self, ch: str) -> str:
        if ch.isspace():
            return ""
        if ch == "\"":
            self._state = "in_string"
            self._escape_pending = False
            self._unicode_pending = None
            return ""
        # Unexpected token; reset.
        self._state = "search_key"
        return ""

    def _in_string(self, ch: str) -> str:
        if self._unicode_pending is not None:
            if ch.lower() in "0123456789abcdef":
                self._unicode_pending.append(ch)
                if len(self._unicode_pending) == 4:
                    try:
                        codepoint = int("".join(self._unicode_pending), 16)
                        emitted = chr(codepoint)
                    except Exception:
                        emitted = ""
                    self._unicode_pending = None
                    self._escape_pending = False
                    return emitted
                return ""
            # Invalid unicode escape; drop.
            self._unicode_pending = None
            self._escape_pending = False
            return ""

        if self._escape_pending:
            self._escape_pending = False
            if ch == "u":
                self._unicode_pending = []
                return ""
            mapping = {
                "\"": "\"",
                "\\": "\\",
                "/": "/",
                "b": "\b",
                "f": "\f",
                "n": "\n",
                "r": "\r",
                "t": "\t",
            }
            return mapping.get(ch, ch)

        if ch == "\\":
            self._escape_pending = True
            return ""
        if ch == "\"":
            self._state = "search_key"
            return ""
        return ch


class TitleService:
    """Generates short conversation titles and stores them if absent."""

    def __init__(
        self,
        conversation_service: ConversationService,
        *,
        model: str = "gpt-5-nano",
        timeout_seconds: float = 5.0,
        stream_runner: Callable[[Agent, str], _RunnerStream] | None = None,
    ) -> None:
        self._conversation_service = conversation_service
        self._timeout_seconds = timeout_seconds
        self._agent = _default_agent(model)
        self._stream_runner = stream_runner or Runner.run_streamed

    async def stream_title(
        self,
        *,
        conversation_id: str,
        tenant_id: str,
        first_user_message: str,
    ) -> AsyncIterator[str]:
        """Stream the generated title and persist it once complete.

        Yields only title text deltas (not JSON envelope). The caller is expected
        to wrap these in SSE (`data: ...\\n\\n`).
        """

        message = (first_user_message or "").strip()
        if not message:
            return

        stream: _RunnerStream | None = None
        extracted_so_far: list[str] = []
        extractor = _JsonStringFieldExtractor("title")

        try:
            stream = self._stream_runner(self._agent, message)

            async with asyncio.timeout(self._timeout_seconds):
                async for event in stream.stream_events():
                    if getattr(event, "type", None) != "raw_response_event":
                        continue
                    raw = getattr(event, "data", None)
                    if getattr(raw, "type", None) != "response.output_text.delta":
                        continue
                    delta = getattr(raw, "delta", None)
                    if not isinstance(delta, str) or not delta:
                        continue
                    chunk = extractor.feed(delta)
                    if not chunk:
                        continue
                    # SSE `data:` lines are newline-delimited; avoid breaking the frame.
                    chunk = chunk.replace("\r", " ").replace("\n", " ")
                    extracted_so_far.append(chunk)
                    yield chunk

        except TimeoutError:
            logger.warning(
                "title_generation.timeout",
                extra={"conversation_id": conversation_id, "tenant_id": tenant_id},
            )
            return
        except asyncio.CancelledError:  # client disconnected, server shutdown, etc.
            raise
        except Exception:
            logger.exception(
                "title_generation.error",
                extra={"conversation_id": conversation_id, "tenant_id": tenant_id},
            )
            return

        final_output = getattr(stream, "final_output", None) if stream is not None else None
        title_text = self._extract_title(final_output)
        if not title_text:
            title_text = self._extract_title("".join(extracted_so_far))

        if not title_text:
            return

        # Persist once (best-effort). A parallel request may win; that's okay.
        try:
            await self._conversation_service.set_display_name(
                conversation_id,
                tenant_id=tenant_id,
                display_name=title_text,
                generated_at=datetime.now(UTC),
            )
        except Exception:
            logger.exception(
                "title_generation.persist_failed",
                extra={"conversation_id": conversation_id, "tenant_id": tenant_id},
            )

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
        normalized = re.sub(r"^[\"'“”]+|[\"'“”]+$", "", normalized)
        normalized = " ".join(normalized.split())  # collapse whitespace

        if not normalized:
            return None

        if len(normalized) > 60:
            normalized = normalized[:60].rstrip()

        return normalized


def get_title_service() -> TitleService:
    """Resolve the container-backed title service."""

    from app.bootstrap.container import get_container, wire_title_service

    container = get_container()
    if getattr(container, "title_service", None) is None:
        wire_title_service(container)
    svc = container.title_service
    if svc is None:  # pragma: no cover - defensive
        raise RuntimeError("TitleService is not configured")
    return svc


__all__ = ["TitleService", "get_title_service"]
