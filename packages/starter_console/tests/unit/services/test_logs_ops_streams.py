from __future__ import annotations

import threading
from pathlib import Path

import io

from starter_console.ports.console import ConsolePort
from starter_console.services.infra import logs_ops


class DummyConsole(ConsolePort):
    def __init__(self) -> None:
        self.messages: list[str] = []
        self.stream = io.StringIO()
        self.err_stream = io.StringIO()

    def info(self, message: str, topic: str | None = None, *, stream=None) -> None:
        del topic, stream
        self.messages.append(message)

    def warn(self, message: str, topic: str | None = None, *, stream=None) -> None:
        del topic, stream
        self.messages.append(message)

    def error(self, message: str, topic: str | None = None, *, stream=None) -> None:
        del topic, stream
        self.messages.append(message)

    def success(self, message: str, topic: str | None = None, *, stream=None) -> None:
        del topic, stream
        self.messages.append(message)

    def note(self, message: str, topic: str | None = None) -> None:
        del topic
        self.messages.append(message)

    def section(self, title: str, subtitle: str | None = None, *, icon: str = "◆") -> None:
        del subtitle, icon
        self.messages.append(title)

    def step(self, prefix: str, message: str) -> None:
        self.messages.append(f"{prefix} {message}")

    def value_change(
        self,
        *,
        scope: str | None,
        key: str,
        previous: str | None,
        current: str,
        secret: bool = False,
    ) -> None:
        del scope, secret
        self.messages.append(f"{key}: {previous} -> {current}")

    def newline(self) -> None:
        self.messages.append("")

    def print(self, *renderables, **kwargs) -> None:
        del kwargs
        self.messages.append(" ".join(str(item) for item in renderables))

    def render(self, renderable, *, error: bool = False) -> None:
        del error
        self.messages.append(str(renderable))

    def rule(self, title: str) -> None:
        self.messages.append(title)

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


class DummyProcess:
    def __init__(self) -> None:
        self.stdout = ["line-one\n", "line-two\n"]
        self._terminated = False
        self._killed = False
        self._returncode: int | None = None

    def poll(self) -> int | None:
        return self._returncode

    def terminate(self) -> None:
        self._terminated = True

    def kill(self) -> None:
        self._killed = True
        self._returncode = -9

    def wait(self, timeout: float | None = None) -> int | None:
        del timeout
        if self._terminated and self._returncode is None:
            self._returncode = 0
        return self._returncode

    def __enter__(self) -> DummyProcess:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def test_start_stream_returns_stream_and_logs(monkeypatch, tmp_path: Path) -> None:
    process = DummyProcess()
    monkeypatch.setattr(logs_ops.subprocess, "Popen", lambda *args, **kwargs: process)

    console = DummyConsole()
    errors: list[str] = []
    target = logs_ops.TailTarget(name="api", command=["tail", "-f", "file"], cwd=tmp_path)

    stream = logs_ops.start_stream(console, target, errors)
    assert stream is not None
    assert isinstance(stream.thread, threading.Thread)

    stream.thread.join(timeout=1)
    assert errors == []
    assert console.messages

    logs_ops.stop_streams([stream])
    assert process._terminated is True


def test_start_stream_handles_missing_binary(monkeypatch, tmp_path: Path) -> None:
    def _raise(*_args, **_kwargs):
        raise FileNotFoundError("missing")

    monkeypatch.setattr(logs_ops.subprocess, "Popen", _raise)

    console = DummyConsole()
    errors: list[str] = []
    target = logs_ops.TailTarget(name="api", command=["tail", "-f"], cwd=tmp_path)

    stream = logs_ops.start_stream(console, target, errors)
    assert stream is None
    assert errors
