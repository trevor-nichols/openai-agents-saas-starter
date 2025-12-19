"""Session and provider conversation lifecycle helpers."""

from __future__ import annotations

import logging
import math
from collections.abc import Awaitable, Callable, Mapping
from datetime import UTC, datetime
from typing import Any

from app.domain.conversations import ConversationSessionState
from app.infrastructure.providers.openai.memory import (
    MemoryStrategy,
    MemoryStrategyConfig,
    StrategySession,
)
from app.services.agents.policy import AgentRuntimePolicy
from app.services.conversation_service import ConversationService

logger = logging.getLogger(__name__)


class SessionManager:
    """Coordinates provider conversation ids and SDK session handles."""

    def __init__(
        self,
        conversation_service: ConversationService,
        policy: AgentRuntimePolicy,
    ) -> None:
        self._conversation_service = conversation_service
        self._policy = policy

    async def resolve_provider_conversation_id(
        self,
        *,
        provider: Any,
        actor,
        conversation_id: str,
        existing_state: ConversationSessionState | None,
    ) -> str | None:
        if existing_state and existing_state.provider_conversation_id:
            if existing_state.provider_conversation_id.startswith("conv_"):
                return existing_state.provider_conversation_id
            logger.warning(
                "Ignoring non-conv provider conversation id for conversation %s: %s",
                conversation_id,
                existing_state.provider_conversation_id,
            )

        if self._policy.disable_provider_conversation_creation:
            return None

        factory = getattr(provider, "conversation_factory", None)
        if not factory:
            return None

        try:
            candidate = await factory.create(
                tenant_id=actor.tenant_id,
                user_id=actor.user_id,
                conversation_key=conversation_id,
            )
            if not (candidate or "").startswith("conv_"):
                logger.warning(
                    "Provider conversation id did not match expected format; ignoring: %s",
                    candidate,
                )
                return None
            return candidate
        except Exception:  # pragma: no cover - defensive fallback
            logger.exception(
                "Failed to create provider conversation; proceeding without conv id.",
            )
            return None

    async def acquire_session(
        self,
        provider: Any,
        tenant_id: str,
        conversation_id: str,
        provider_conversation_id: str | None,
        memory_strategy: MemoryStrategyConfig | None = None,
        agent_key: str | None = None,
        on_compaction: Callable[[Mapping[str, Any]], Awaitable[None]] | None = None,
    ) -> tuple[str, Any]:
        state = await self._conversation_service.get_session_state(
            conversation_id, tenant_id=tenant_id
        )
        if provider_conversation_id and (
            self._policy.force_provider_session_rebind or not (state and state.sdk_session_id)
        ):
            session_id = provider_conversation_id
        elif state and state.sdk_session_id:
            session_id = state.sdk_session_id
        else:
            session_id = conversation_id

        session_handle = provider.session_store.build(session_id)
        if memory_strategy and _is_session_handle(session_handle):
            on_summary = None
            if memory_strategy.mode == MemoryStrategy.SUMMARIZE:

                async def _persist(summary_text: str) -> None:
                    length_tokens = (
                        max(1, math.ceil(len(summary_text) / 4)) if summary_text else None
                    )
                    await self._conversation_service.persist_summary(
                        conversation_id,
                        tenant_id=tenant_id,
                        agent_key=agent_key,
                        summary_text=summary_text,
                        summary_model=memory_strategy.summarizer_model,
                        version="v1",
                        summary_length_tokens=length_tokens,
                    )

                on_summary = _persist

            session_handle = StrategySession(
                session_handle,
                memory_strategy,
                on_summary=on_summary,
                on_compaction=on_compaction,
            )
            logger.info(
                "session.memory_strategy_applied",
                extra={
                    "conversation_id": conversation_id,
                    "tenant_id": tenant_id,
                    "strategy": memory_strategy.mode.value,
                },
            )
        return session_id, session_handle

    async def sync_session_state(
        self,
        *,
        tenant_id: str,
        conversation_id: str,
        session_id: str,
        provider_name: str | None,
        provider_conversation_id: str | None,
    ) -> None:
        await self._conversation_service.update_session_state(
            conversation_id,
            tenant_id=tenant_id,
            state=ConversationSessionState(
                provider=provider_name,
                provider_conversation_id=provider_conversation_id,
                sdk_session_id=session_id,
                last_session_sync_at=datetime.now(UTC),
            ),
        )


def _is_session_handle(obj: Any) -> bool:
    return hasattr(obj, "get_items") and hasattr(obj, "add_items")


__all__ = ["SessionManager"]
