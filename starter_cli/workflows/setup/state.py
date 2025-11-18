"""Persistence helpers for wizard progress + prompt outcomes."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class WizardStateStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data: dict[str, Any] = {
            "version": 1,
            "answers": {},
            "skipped": {},
        }
        if path.exists():
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                payload = {}
            if isinstance(payload, dict):
                self.data.update(
                    {
                        "version": payload.get("version", 1),
                        "answers": payload.get("answers", {}) or {},
                        "skipped": payload.get("skipped", {}) or {},
                    }
                )

    def record_answer(self, key: str, value: str) -> None:
        self.data["answers"][_normalize(key)] = {
            "value": value,
            "recorded_at": _timestamp(),
        }
        self.data["skipped"].pop(_normalize(key), None)
        self._save()

    def record_skip(self, key: str, reason: str) -> None:
        self.data["skipped"][_normalize(key)] = {
            "reason": reason,
            "recorded_at": _timestamp(),
        }
        self._save()

    def snapshot(self) -> dict[str, str]:
        snapshot: dict[str, str] = {}
        for key, payload in self.data.get("answers", {}).items():
            value = payload.get("value")
            if isinstance(value, str):
                snapshot[key] = value
        return snapshot

    def _save(self) -> None:
        self.path.write_text(
            json.dumps(self.data, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _normalize(key: str) -> str:
    return key.strip().upper()


__all__ = ["WizardStateStore"]
