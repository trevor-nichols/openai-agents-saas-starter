"""Session and provider conversation lifecycle helpers."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from app.domain.conversations import ConversationSessionState
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


__all__ = ["SessionManager"]
