"""Cursor helpers for keyset pagination."""

from __future__ import annotations

import base64
import json
import uuid
from datetime import datetime


def encode_list_cursor(ts: datetime, conversation_id: uuid.UUID) -> str:
    payload = {"ts": ts.isoformat(), "id": str(conversation_id)}
    raw = json.dumps(payload).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8")


def decode_list_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    try:
        data = json.loads(base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8"))
        ts = datetime.fromisoformat(data["ts"])
        conv_id = uuid.UUID(data["id"])
        return ts, conv_id
    except Exception as exc:  # pragma: no cover - invalid cursor input
        raise ValueError("Invalid pagination cursor") from exc


def encode_search_cursor(rank: float, ts: datetime, conversation_id: uuid.UUID) -> str:
    payload = {"rank": rank, "ts": ts.isoformat(), "id": str(conversation_id)}
    raw = json.dumps(payload).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8")


def decode_search_cursor(cursor: str) -> tuple[float, datetime, uuid.UUID]:
    try:
        data = json.loads(base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8"))
        rank = float(data["rank"])
        ts = datetime.fromisoformat(data["ts"])
        conv_id = uuid.UUID(data["id"])
        return rank, ts, conv_id
    except Exception as exc:  # pragma: no cover - invalid cursor input
        raise ValueError("Invalid search pagination cursor") from exc


def encode_message_cursor(ts: datetime, message_id: int) -> str:
    payload = {"ts": ts.isoformat(), "id": message_id}
    raw = json.dumps(payload).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8")


def decode_message_cursor(cursor: str) -> tuple[datetime, int]:
    try:
        data = json.loads(base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8"))
        ts = datetime.fromisoformat(data["ts"])
        message_id = int(data["id"])
        return ts, message_id
    except Exception as exc:  # pragma: no cover - invalid cursor input
        raise ValueError("Invalid messages pagination cursor") from exc


__all__ = [
    "encode_list_cursor",
    "decode_list_cursor",
    "encode_search_cursor",
    "decode_search_cursor",
    "encode_message_cursor",
    "decode_message_cursor",
]
