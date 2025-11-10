from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import TextIO


@dataclass(slots=True)
class Console:
    """Lightweight console helper for consistent CLI messaging."""

    stream: TextIO = sys.stdout
    err_stream: TextIO = sys.stderr

    def info(self, message: str, topic: str | None = None, *, stream: TextIO | None = None) -> None:
        self._write("INFO", message, topic, stream=stream or self.stream)

    def warn(self, message: str, topic: str | None = None, *, stream: TextIO | None = None) -> None:
        self._write("WARN", message, topic, stream=stream or self.err_stream)

    def error(self, message: str, topic: str | None = None, *, stream: TextIO | None = None) -> None:
        self._write("ERROR", message, topic, stream=stream or self.err_stream)

    def success(self, message: str, topic: str | None = None, *, stream: TextIO | None = None) -> None:
        self._write("SUCCESS", message, topic, stream=stream or self.stream)

    def newline(self) -> None:
        print("", file=self.stream)

    def _write(self, level: str, message: str, topic: str | None, *, stream: TextIO) -> None:
        scope = f" [{topic}]" if topic else ""
        print(f"[{level}]{scope} {message}", file=stream)


console = Console()
