"""Runtime context and metadata resolution helpers."""

from __future__ import annotations

import logging
from collections.abc import Mapping

from app.agents._shared.prompt_context import PromptRuntimeContext

logger = logging.getLogger(__name__)


def resolve_runtime_context(
    metadata: Mapping[str, object] | None,
    *,
    bootstrap_ctx: PromptRuntimeContext,
) -> tuple[PromptRuntimeContext, dict[str, object]]:
    """Extract PromptRuntimeContext from metadata and return safe metadata copy."""

    runtime_ctx = None
    safe_metadata: dict[str, object] = {}

    if isinstance(metadata, Mapping):
        runtime_ctx = metadata.get("prompt_runtime_ctx")
        safe_metadata = {k: v for k, v in metadata.items() if k != "prompt_runtime_ctx"}
    elif metadata is not None:
        logger.warning(
            "runtime metadata ignored because it is not a mapping",
            extra={"type": type(metadata).__name__},
        )

    if runtime_ctx is None:
        runtime_ctx = bootstrap_ctx
    elif not isinstance(runtime_ctx, PromptRuntimeContext):
        raise TypeError("prompt_runtime_ctx must be a PromptRuntimeContext")

    return runtime_ctx, safe_metadata


__all__ = ["resolve_runtime_context"]
