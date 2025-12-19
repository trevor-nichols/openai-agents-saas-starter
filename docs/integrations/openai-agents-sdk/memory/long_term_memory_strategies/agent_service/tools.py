from __future__ import annotations

import json
import uuid
from typing import Any, Dict

from .deps import function_tool
from .stores import AUDIT, ORDERS, SCHEDULED, STATE_DIR, TICKETS, utc_now_iso
from .tool_logging import _log_tool_call, _log_tool_event

# --------------------------------------------------------------------------------------
# Function tools (mocked backends)
# --------------------------------------------------------------------------------------


@function_tool
def SearchPolicy(device_model: str) -> str:
    """
    Look up the laptop Refund & Return Policy for a given device model.

    Args:
        device_model: Device identifier/model string (e.g., "MacBook Pro 14", "Dell XPS 13 9310").

    Returns:
        A plain-text policy string.
    """
    policy_path = STATE_DIR / "data" / "policy_data.txt"
    try:
        output_payload = policy_path.read_text(encoding="utf-8").strip()
        if not output_payload:
            raise ValueError("policy data file is empty")
    except Exception as exc:
        output_payload = (
            "Late delivery policy: >5 days late ⇒ reship OR 10% credit. >14 days ⇒ full refund."
        )
        _log_tool_event(f"SearchPolicy fallback; unable to read {policy_path}: {exc}")
    _log_tool_call("SearchPolicy", {"query": device_model}, output_payload)
    return output_payload


@function_tool
def TicketAPI_create(subject: str, body: str, customer_id: str) -> str:
    """Create a new ticket and return its JSON record."""
    t_id = str(uuid.uuid4())[:8]
    TICKETS[t_id] = {
        "id": t_id,
        "subject": subject,
        "body": body,
        "customer_id": customer_id,
        "status": "open",
        "comments": [],
    }
    AUDIT.append(
        {
            "at": utc_now_iso(),
            "event": "ticket.create",
            "ticket": t_id,
        }
    )
    payload = json.dumps(TICKETS[t_id])
    _log_tool_call(
        "TicketAPI_create",
        {"subject": subject, "body": body, "customer_id": customer_id},
        payload,
    )
    return payload


@function_tool
def TicketAPI_comment(ticket_id: str, message: str) -> str:
    """Append a customer-visible comment to a ticket."""
    entry = TICKETS.setdefault(ticket_id, {"id": ticket_id, "comments": []})
    entry.setdefault("status", "open")
    entry["comments"].append(message)
    AUDIT.append(
        {
            "at": utc_now_iso(),
            "event": "ticket.comment",
            "ticket": ticket_id,
            "message": message,
        }
    )
    payload = json.dumps({"ok": True})
    _log_tool_call("TicketAPI_comment", {"ticket_id": ticket_id, "message": message}, payload)
    return payload


@function_tool
def TicketAPI_close(ticket_id: str, reason: str) -> str:
    """Close a ticket with a reason."""
    entry = TICKETS.setdefault(ticket_id, {"id": ticket_id, "comments": []})
    entry["status"] = "closed"
    AUDIT.append(
        {
            "at": utc_now_iso(),
            "event": "ticket.close",
            "ticket": ticket_id,
            "reason": reason,
        }
    )
    payload = json.dumps({"ok": True})
    _log_tool_call("TicketAPI_close", {"ticket_id": ticket_id, "reason": reason}, payload)
    return payload


@function_tool
def GetOrder(order_id: str) -> str:
    """Fetch order details.

    Args:
        order_id: Unique order identifier (e.g., "ORD-12345").

    Returns:
        A JSON string with the shape:
        {
          "found": bool,
          "order_id": "<id>",
          "order": { ... }  # present when found==true, else {}
        }
    """

    payload = """{
                    "found": true,
                    "order_id": "ORD-12345",
                    "order": {
                        "customer_name": "Alex Johnson",
                        "status": "Delivered",
                        "delivery_date": "2025-09-27",
                        "items": [
                        {"sku": "SKU-001", "name": "Wireless Mouse", "qty": 1, "price": 29.99},
                        {"sku": "SKU-002", "name": "Laptop Stand", "qty": 1, "price": 45.00}
                        ],
                        "shipping_address": "123 Elm Street, Springfield, IL 62701",
                        "total_amount": 74.99,
                        "policy_tags": ["LateDeliveryEligible", "Refundable"],
                        "sla_days": 5
                    }
                    }
                    """
    _log_tool_call("GetOrder", {"order_id": order_id}, payload)
    return payload


@function_tool
def Scheduler_run_at(iso_time: str, task_name: str, payload_json: str = "{}") -> str:
    """Schedule a follow-up task (demo: store in memory; prod: push to queue/cron)."""
    try:
        payload_obj = json.loads(payload_json) if payload_json else {}
    except json.JSONDecodeError:
        payload_obj = {"raw": payload_json}

    if not isinstance(payload_obj, dict):
        payload_obj = {"value": payload_obj}

    entry: Dict[str, Any] = {
        "id": str(uuid.uuid4())[:8],
        "iso_time": iso_time,
        "task_name": task_name,
        "payload": payload_obj,
    }
    SCHEDULED.append(entry)
    AUDIT.append(
        {
            "at": utc_now_iso(),
            "event": "scheduler.enqueue",
            **entry,
        }
    )
    payload = json.dumps(entry)
    _log_tool_call(
        "Scheduler_run_at",
        {"iso_time": iso_time, "task_name": task_name, "payload_json": payload_json},
        payload,
    )
    return payload


# Tool registry (preserve original defaults: some tools are intentionally disabled)
TOOL_REGISTRY = {
    "SearchPolicy": SearchPolicy,
    # "TicketAPI_create": TicketAPI_create,
    # "TicketAPI_comment": TicketAPI_comment,
    # "TicketAPI_close": TicketAPI_close,
    "GetOrder": GetOrder,
    # "Scheduler_run_at": Scheduler_run_at,
}

__all__ = [
    "SearchPolicy",
    "TicketAPI_create",
    "TicketAPI_comment",
    "TicketAPI_close",
    "GetOrder",
    "Scheduler_run_at",
    "TOOL_REGISTRY",
]
