from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from app.domain.ai.models import AgentRunUsage

from ..streaming import PublicUsage, WorkflowContext


def now_iso() -> str:
    return datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")


def coerce_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    try:
        return str(value)
    except Exception:
        return None


def safe_json_parse(value: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(value)
    except Exception:
        return None
    return parsed if isinstance(parsed, dict) else None


def as_dict(value: Any) -> dict[str, Any] | None:
    return value if isinstance(value, dict) else None


def extract_urls(obj: Any, *, limit: int = 50) -> list[str]:
    found: list[str] = []

    def _walk(value: Any) -> None:
        if len(found) >= limit:
            return
        if isinstance(value, dict):
            url = value.get("url")
            if isinstance(url, str) and url:
                found.append(url)
            for child in value.values():
                _walk(child)
            return
        if isinstance(value, list):
            for child in value:
                _walk(child)

    _walk(obj)
    return found


def workflow_context_from_meta(meta: Mapping[str, Any] | None) -> WorkflowContext | None:
    if not meta:
        return None
    branch_index = meta.get("branch_index")
    return WorkflowContext(
        workflow_key=coerce_str(meta.get("workflow_key")),
        workflow_run_id=coerce_str(meta.get("workflow_run_id")),
        stage_name=coerce_str(meta.get("stage_name")),
        step_name=coerce_str(meta.get("step_name")),
        step_agent=coerce_str(meta.get("step_agent")),
        parallel_group=coerce_str(meta.get("parallel_group")),
        branch_index=branch_index if isinstance(branch_index, int) else None,
    )


def agent_tool_names_from_meta(meta: Mapping[str, Any] | None) -> set[str]:
    if not meta:
        return set()
    raw = meta.get("agent_tool_names")
    if not isinstance(raw, list):
        return set()
    names = {name for name in raw if isinstance(name, str) and name}
    return names


def agent_tool_name_map_from_meta(meta: Mapping[str, Any] | None) -> dict[str, str]:
    if not meta:
        return {}
    raw = meta.get("agent_tool_name_map")
    if not isinstance(raw, Mapping):
        return {}
    return {
        key: value
        for key, value in raw.items()
        if isinstance(key, str) and key and isinstance(value, str) and value
    }


def usage_to_public(usage: AgentRunUsage | None) -> PublicUsage | None:
    if usage is None:
        return None
    return PublicUsage(
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        total_tokens=usage.total_tokens,
        cached_input_tokens=usage.cached_input_tokens,
        reasoning_output_tokens=usage.reasoning_output_tokens,
        requests=usage.requests,
    )
