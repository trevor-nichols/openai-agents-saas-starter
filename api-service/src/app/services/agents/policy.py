"""Runtime policy toggles for agent orchestration.

Encapsulates environment-driven switches so they can be injected and tested
without patching global env lookups inside the service layer.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True)
class AgentRuntimePolicy:
    allow_openai_uuid_fallback: bool = False
    disable_provider_conversation_creation: bool = False
    force_provider_session_rebind: bool = False

    @classmethod
    def from_env(cls) -> AgentRuntimePolicy:
        """Construct policy values from environment flags.

        Keeping this small and explicit lets tests override behavior by
        injecting a policy instance instead of patching os.environ.
        """

        def _flag(name: str) -> bool:
            return os.getenv(name, "").lower() in {"1", "true", "yes"}

        return cls(
            allow_openai_uuid_fallback=_flag("ALLOW_OPENAI_CONVERSATION_UUID_FALLBACK"),
            disable_provider_conversation_creation=_flag("DISABLE_PROVIDER_CONVERSATION_CREATION"),
            force_provider_session_rebind=_flag("FORCE_PROVIDER_SESSION_REBIND"),
        )


__all__ = ["AgentRuntimePolicy"]
