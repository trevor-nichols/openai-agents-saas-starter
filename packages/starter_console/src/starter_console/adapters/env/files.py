"""Env file helpers shared across CLI commands."""

from __future__ import annotations

import json
import os
import re
from collections.abc import Iterable
from pathlib import Path


class EnvFile:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.lines: list[str] = []
        if path.exists():
            self.lines = path.read_text(encoding="utf-8").splitlines()
        self._index: dict[str, int] = {}
        self._dirty = False
        self._reindex()

    def _reindex(self) -> None:
        self._index.clear()
        for idx, line in enumerate(self.lines):
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, _ = stripped.split("=", 1)
            self._index[key.strip()] = idx

    def get(self, key: str) -> str | None:
        idx = self._index.get(key)
        if idx is None:
            return None
        _, value = self._split_line(self.lines[idx])
        return value

    def set(self, key: str, value: str) -> None:
        serialized = self._serialize_value(value)
        idx = self._index.get(key)
        entry = f"{key}={serialized}"
        if idx is None:
            self.lines.append(entry)
            self._index[key] = len(self.lines) - 1
        else:
            self.lines[idx] = entry
        self._dirty = True

    def delete(self, key: str) -> None:
        idx = self._index.pop(key, None)
        if idx is None:
            return
        self.lines.pop(idx)
        self._dirty = True
        self._reindex()

    def save(self) -> None:
        if not self._dirty:
            return
        body = "\n".join(self.lines)
        if not body.endswith("\n"):
            body += "\n"
        self.path.write_text(body, encoding="utf-8")
        self._dirty = False

    def as_dict(self) -> dict[str, str]:
        data: dict[str, str] = {}
        for key in self._index:
            value = self.get(key)
            if value is not None:
                data[key] = value
        return data

    @staticmethod
    def _split_line(line: str) -> tuple[str, str]:
        if "=" not in line:
            return line, ""
        key, value = line.split("=", 1)
        return key.strip(), EnvFile._unquote(value.strip())

    @staticmethod
    def _unquote(value: str) -> str:
        if not value:
            return ""
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            if value.startswith('"'):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    pass
            return value[1:-1]
        if value.startswith('""') and value.endswith('""'):
            return value[3:-3]
        if " #" in value:
            value = value.split(" #", 1)[0]
        return value.strip()

    @staticmethod
    def _serialize_value(value: str) -> str:
        if value == "":
            return '""'
        safe = all(ch.isalnum() or ch in "_.:@/-" for ch in value)
        return value if safe else json.dumps(value)


ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


def aggregate_env_values(files: Iterable[EnvFile], keys: Iterable[str]) -> dict[str, str | None]:
    aggregated: dict[str, str | None] = {key: None for key in keys}
    for file in files:
        for key in keys:
            if aggregated[key]:
                continue
            aggregated[key] = file.get(key)
    for key in keys:
        if aggregated[key]:
            continue
        aggregated[key] = os.environ.get(key)
    return aggregated


def build_env_scope(files: Iterable[EnvFile]) -> dict[str, str]:
    scope: dict[str, str] = {}
    for file in files:
        scope.update(file.as_dict())
    for key, value in os.environ.items():
        scope.setdefault(key, value)
    return scope


def expand_env_placeholders(value: str, scope: dict[str, str]) -> str:
    def replacer(match: re.Match[str]) -> str:
        key = match.group(1)
        return scope.get(key) or os.environ.get(key) or match.group(0)

    return ENV_PATTERN.sub(replacer, value)
