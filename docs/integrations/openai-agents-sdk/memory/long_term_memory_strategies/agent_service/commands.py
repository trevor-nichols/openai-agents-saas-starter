from __future__ import annotations

from typing import Any, Dict

from .runtime import (
    SESSIONS,
    configure_compacting_sessions,
    configure_summarizing_sessions,
    configure_trimming_sessions,
    run_agent,
)
from .stores import reset_data_stores


async def handle_command(payload: Dict[str, Any]) -> Dict[str, Any]:
    cmd_type = payload.get("type")

    if cmd_type == "run":
        agent_id = payload["agent_id"]
        message = payload["message"]
        history = payload.get("history", [])
        config = payload.get("config", {})
        return await run_agent(agent_id=agent_id, message=message, history=history, config=config)

    if cmd_type == "configure_summarization":
        agent_ids = payload.get("agent_ids") or []
        if not isinstance(agent_ids, list):
            raise ValueError("agent_ids must be a list")
        enable = bool(payload.get("enable"))
        max_turns = payload.get("max_turns")
        keep_last = payload.get("keep_last")
        configure_summarizing_sessions(agent_ids, enable, max_turns=max_turns, keep_last=keep_last)
        return {"ok": True}

    if cmd_type == "configure_trimming":
        agent_ids = payload.get("agent_ids") or []
        if not isinstance(agent_ids, list):
            raise ValueError("agent_ids must be a list")
        enable = bool(payload.get("enable"))
        max_turns = payload.get("max_turns")
        keep_last = payload.get("keep_last")
        configure_trimming_sessions(agent_ids, enable, max_turns, keep_last=keep_last)
        return {"ok": True}

    if cmd_type == "configure_compacting":
        agent_ids = payload.get("agent_ids") or []
        if not isinstance(agent_ids, list):
            raise ValueError("agent_ids must be a list")
        enable = bool(payload.get("enable"))
        trigger = payload.get("trigger")
        keep = payload.get("keep")
        exclude_tools = payload.get("exclude_tools")
        clear_tool_inputs = payload.get("clear_tool_inputs")
        configure_compacting_sessions(
            agent_ids,
            enable,
            trigger=trigger if isinstance(trigger, dict) else None,
            keep=keep,
            exclude_tools=exclude_tools,
            clear_tool_inputs=clear_tool_inputs,
        )
        return {"ok": True}

    if cmd_type == "reset":
        reset_data_stores()
        SESSIONS.clear()
        return {"ok": True}

    raise ValueError(f"Unsupported command type: {cmd_type}")
