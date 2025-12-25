from __future__ import annotations

import sys
import threading


class BufferConsole:
    def __init__(self, *, max_lines: int = 500) -> None:
        self.messages: list[str] = []
        self.stream = sys.stdout
        self.err_stream = sys.stderr
        self._lock = threading.Lock()
        self._max_lines = max_lines

    def info(self, message: str, topic: str | None = None, *, stream=None) -> None:
        del stream
        prefix = f"[{topic}] " if topic else ""
        self._append(f"INFO {prefix}{message}")

    def warn(self, message: str, topic: str | None = None, *, stream=None) -> None:
        del stream
        prefix = f"[{topic}] " if topic else ""
        self._append(f"WARN {prefix}{message}")

    def error(self, message: str, topic: str | None = None, *, stream=None) -> None:
        del stream
        prefix = f"[{topic}] " if topic else ""
        self._append(f"ERROR {prefix}{message}")

    def success(self, message: str, topic: str | None = None, *, stream=None) -> None:
        del stream
        prefix = f"[{topic}] " if topic else ""
        self._append(f"SUCCESS {prefix}{message}")

    def note(self, message: str, topic: str | None = None) -> None:
        prefix = f"[{topic}] " if topic else ""
        self._append(f"NOTE {prefix}{message}")

    def section(self, title: str, subtitle: str | None = None, *, icon: str = "*") -> None:
        detail = f" - {subtitle}" if subtitle else ""
        self._append(f"{icon} {title}{detail}")

    def step(self, prefix: str, message: str) -> None:
        self._append(f"{prefix} {message}")

    def value_change(
        self,
        *,
        scope: str | None,
        key: str,
        previous: str | None,
        current: str,
        secret: bool = False,
    ) -> None:
        del secret
        scope_label = f"[{scope}] " if scope else ""
        self._append(f"{scope_label}{key}: {previous} -> {current}")

    def newline(self) -> None:
        self._append("")

    def print(self, *renderables, **kwargs) -> None:
        del kwargs
        self._append(" ".join(str(item) for item in renderables))

    def render(self, renderable, *, error: bool = False) -> None:
        prefix = "ERROR " if error else ""
        self._append(f"{prefix}{renderable}")

    def rule(self, title: str) -> None:
        self._append(f"---- {title} ----")

    def ask_text(
        self,
        *,
        key: str,
        prompt: str,
        default: str | None,
        required: bool,
        secret: bool = False,
        command_hook=None,
    ) -> str:
        del key, prompt, required, secret, command_hook
        return default or ""

    def ask_bool(
        self,
        *,
        key: str,
        prompt: str,
        default: bool,
        command_hook=None,
    ) -> bool:
        del key, prompt, command_hook
        return default

    def snapshot(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(self.messages)

    def clear(self) -> None:
        with self._lock:
            self.messages.clear()

    def _append(self, message: str) -> None:
        with self._lock:
            self.messages.append(message)
            if len(self.messages) > self._max_lines:
                self.messages = self.messages[-self._max_lines :]


__all__ = ["BufferConsole"]
