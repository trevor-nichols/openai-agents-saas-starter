"""Projection of SDK run items into the structured event log."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any

from app.domain.ai.models import AgentStreamEvent
from app.domain.conversations import ConversationEvent
from app.services.conversation_service import ConversationService
from app.utils.tools.builtin_tools import infer_builtin_tool_name


class EventProjector:
    """Maps SDK session items into ConversationEvent rows."""

    def __init__(self, conversation_service: ConversationService) -> None:
        self._conversations = conversation_service

    async def ingest_session_items(
        self,
        *,
        conversation_id: str,
        tenant_id: str,
        session_items: Sequence[Mapping[str, Any]],
        agent: str | None,
        model: str | None,
        response_id: str | None,
        workflow_run_id: str | None = None,
    ) -> None:
        events = [
            self._map_item(
                _to_mapping(item),
                agent=agent,
                model=model,
                response_id=response_id,
                workflow_run_id=workflow_run_id,
            )
            for item in session_items
        ]
        # Filter out items we failed to map (None)
        filtered = [ev for ev in events if ev is not None]
        await self._conversations.append_run_events(
            conversation_id,
            tenant_id=tenant_id,
            events=filtered,
        )

    @staticmethod
    def _map_item(
        item: Mapping[str, Any],
        *,
        agent: str | None,
        model: str | None,
        response_id: str | None,
        workflow_run_id: str | None,
    ) -> ConversationEvent | None:
        explicit_run_item_type = item.get("run_item_type")
        item_type = str(item.get("type") or explicit_run_item_type or "unknown")
        role = item.get("role")
        role_literal = role if role in {"user", "assistant", "system"} else None
        run_item_type = (
            str(explicit_run_item_type)
            if explicit_run_item_type
            else _classify_item_type(item_type, role_literal)
        )

        tool_call_id = None
        tool_name = None
        if run_item_type in {"tool_call", "tool_result", "mcp_call"}:
            tool_call_id = item.get("tool_call_id") or item.get("id") or None
            tool_name = item.get("tool_name") or item.get("name") or None
            if tool_name is None:
                tool_name = infer_builtin_tool_name(item_type)

        content_text = _extract_text(item)
        reasoning_text = _extract_reasoning(item)

        call_arguments = _maybe_json(item.get("arguments"))
        call_output = _maybe_json(item.get("output") or item.get("result"))
        if call_arguments is None and run_item_type == "tool_call":
            # Best-effort arguments for built-in tool run items emitted by Responses API.
            if item_type == "web_search_call":
                call_arguments = _maybe_json(item.get("action"))
            elif item_type == "file_search_call":
                call_arguments = _maybe_json({"queries": item.get("queries")})
            elif item_type == "code_interpreter_call":
                call_arguments = _maybe_json({"code": item.get("code")})
            elif item_type == "image_generation_call":
                call_arguments = _maybe_json(
                    {
                        "prompt": item.get("prompt") or item.get("revised_prompt"),
                        "size": item.get("size"),
                        "quality": item.get("quality"),
                        "background": item.get("background"),
                    }
                )
        if (
            call_output is None
            and run_item_type == "tool_call"
            and infer_builtin_tool_name(item_type)
        ):
            # Persist tool completion status even when the provider does not emit a separate
            # tool-result item.
            status = item.get("status")
            if status is not None:
                call_output = _maybe_json({"status": status})

        timestamp = _extract_timestamp(item)

        agent_value = agent
        if agent_value is None:
            agent_value = item.get("agent") or item.get("agent_key")

        model_value = model
        if model_value is None:
            model_value = item.get("model") or item.get("model_id")

        return ConversationEvent(
            run_item_type=run_item_type,
            run_item_name=item.get("name") if isinstance(item.get("name"), str) else None,
            role=role_literal,
            agent=str(agent_value) if agent_value is not None else None,
            tool_call_id=str(tool_call_id) if tool_call_id else None,
            tool_name=str(tool_name) if tool_name else None,
            model=str(model_value) if model_value is not None else None,
            content_text=content_text,
            reasoning_text=reasoning_text,
            call_arguments=call_arguments,
            call_output=call_output,
            attachments=[],
            response_id=response_id,
            workflow_run_id=workflow_run_id,
            timestamp=timestamp,
        )


def _classify_item_type(item_type: str, role: Any) -> str:
    if item_type in {"message", "response.message", "response_message"}:
        if role == "user":
            return "user_message"
        if role == "system":
            return "system_message"
        return "assistant_message"
    if infer_builtin_tool_name(item_type):
        # Built-in Responses tool run items like `web_search_call`.
        return "tool_call"
    if item_type in {"tool_call", "function_call", "tool_call_item"}:
        return "tool_call"
    if item_type in {"tool_result", "tool_output", "function_result", "tool_output_item"}:
        return "tool_result"
    if item_type in {"mcp_call"}:
        return "mcp_call"
    if "reasoning" in item_type:
        return "reasoning"
    return item_type


def _extract_text(item: Mapping[str, Any]) -> str | None:
    content = item.get("content")
    if content is None:
        return None
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            if isinstance(part, dict):
                if "text" in part and isinstance(part["text"], str):
                    parts.append(part["text"])
                elif "content" in part and isinstance(part["content"], str):
                    parts.append(part["content"])
        return "".join(parts) if parts else None
    if isinstance(content, Mapping):
        text = content.get("text")
        if isinstance(text, str):
            return text
    return None


def _extract_reasoning(item: Mapping[str, Any]) -> str | None:
    if "reasoning" in item and isinstance(item["reasoning"], str):
        return item["reasoning"]
    if "delta" in item and "reasoning" in str(item.get("type", "")):
        delta = item.get("delta")
        if isinstance(delta, str):
            return delta
    return None


def _maybe_json(value: Any) -> Mapping[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, Mapping):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, Mapping):
                return parsed
        except Exception:
            return {"value": value}
    return {"value": value}


def _extract_timestamp(item: Mapping[str, Any]) -> datetime:
    ts = item.get("created_at") or item.get("timestamp")
    if isinstance(ts, datetime):
        return ts
    return datetime.utcnow()


def _to_mapping(obj: Any) -> Mapping[str, Any]:
    if isinstance(obj, Mapping):
        return obj
    mapped = AgentStreamEvent._to_mapping(obj)
    return mapped or {}


__all__ = ["EventProjector"]
