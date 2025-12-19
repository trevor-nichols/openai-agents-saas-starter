from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# --------------------------------------------------------------------------------------
# Mocked data stores
# --------------------------------------------------------------------------------------

KB: List[Dict[str, Any]] = [
    {
        "id": "policy_late_shipping",
        "tags": ["shipping", "sla"],
        "text": (
            "Late delivery policy: >5 days late ⇒ reship OR 10% credit. >14 days ⇒ full refund."
        ),
    },
    {
        "id": "policy_refund_limits",
        "tags": ["refund", "risk"],
        "text": (
            "Refunds ≤$200 auto; $200–$1000 require approval; >$1000 escalate to human."
        ),
    },
]

TICKETS: Dict[str, Dict[str, Any]] = {}
ORDERS: Dict[str, Dict[str, Any]] = {
    "12345": {"status": "in_transit", "days_late": 7, "value": 150.0, "currency": "USD"}
}

APPROVALS: Dict[str, Dict[str, Any]] = {}
SCHEDULED: List[Dict[str, Any]] = []
AUDIT: List[Dict[str, Any]] = []

# Keep the same relative layout as the original single-file module.
STATE_DIR = (Path(__file__).resolve().parent.parent) / "state"
SUMMARY_OUTPUT_DIR = STATE_DIR / "summaries"
SUMMARY_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
SUMMARY_FILE_PATH = SUMMARY_OUTPUT_DIR / "summary.txt"

_SUMMARY_CACHE: Optional[str] = None
_SUMMARY_CACHE_MTIME: Optional[float] = None


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _extract_summary_section(raw: str) -> Optional[str]:
    if not raw:
        return None

    lowered = raw.lower()
    marker = "summary:"
    idx = lowered.rfind(marker)
    if idx == -1:
        return None

    start = idx + len(marker)
    summary_text = raw[start:].strip()
    return summary_text or None


def _load_cross_session_summary() -> Optional[str]:
    global _SUMMARY_CACHE, _SUMMARY_CACHE_MTIME
    try:
        stat_result = SUMMARY_FILE_PATH.stat()
    except FileNotFoundError:
        _SUMMARY_CACHE = None
        _SUMMARY_CACHE_MTIME = None
        return None
    except OSError:
        return None

    mtime = getattr(stat_result, "st_mtime", None)
    if _SUMMARY_CACHE is not None and mtime is not None and _SUMMARY_CACHE_MTIME == mtime:
        return _SUMMARY_CACHE

    try:
        raw = SUMMARY_FILE_PATH.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        _SUMMARY_CACHE = None
        _SUMMARY_CACHE_MTIME = None
        return None

    summary_text = _extract_summary_section(raw)
    _SUMMARY_CACHE = summary_text
    _SUMMARY_CACHE_MTIME = mtime
    return summary_text


def reset_data_stores() -> None:
    """Return all in-memory data stores to a clean slate."""
    global TICKETS, ORDERS, APPROVALS, SCHEDULED, AUDIT
    TICKETS = {}
    ORDERS = {
        "12345": {"status": "in_transit", "days_late": 7, "value": 150.0, "currency": "USD"}
    }
    APPROVALS = {}
    SCHEDULED = []
    AUDIT = []


def _persist_summary_to_disk(shadow_line: str, summary_text: str) -> None:
    shadow = (shadow_line or "").strip()
    summary = (summary_text or "").strip()
    if not shadow and not summary:
        return

    try:
        SUMMARY_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        file_path = SUMMARY_OUTPUT_DIR / "summary.txt"
        lines = [
            f"generated_at: {utc_now_iso()}",
            "",
        ]
        if shadow:
            lines.append("shadow_line:")
            lines.append(shadow)
            lines.append("")
        if summary:
            lines.append("summary:")
            lines.append(summary)
            lines.append("")

        file_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    except Exception as exc:  # pragma: no cover - best-effort persistence
        print(
            f"[agents-python] Warning: failed to write summary for session: {exc}",
            file=sys.stderr,
        )


__all__ = [
    "KB",
    "TICKETS",
    "ORDERS",
    "APPROVALS",
    "SCHEDULED",
    "AUDIT",
    "STATE_DIR",
    "SUMMARY_OUTPUT_DIR",
    "SUMMARY_FILE_PATH",
    "utc_now_iso",
    "_load_cross_session_summary",
    "reset_data_stores",
    "_persist_summary_to_disk",
]
