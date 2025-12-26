"""Persistence and lifecycle helpers for the CLI-managed dev stack.

This module keeps PID/log metadata under ``var/run/stack.json`` so the CLI can:
- report whether the stack it started is still running,
- stop only the processes it launched, and
- surface log paths and timestamps to the TUI and probes.

It is intentionally side-effect light: no logging, no console output, and no
external dependencies. Callers own user-facing messaging.
"""

from __future__ import annotations

import json
import os
import signal
import tempfile
import time
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path

from starter_console.core.constants import PROJECT_ROOT
from starter_console.workflows.home.process_utils import terminate_process_tree
from starter_console.workflows.home.runtime import resolve_pidfile

STACK_STATE_PATH = resolve_pidfile(PROJECT_ROOT)


@dataclass(slots=True)
class StackProcess:
    label: str
    pid: int
    command: Sequence[str]
    log_path: str | None = None
    isolated: bool = False
    pgid: int | None = None
    started_at: float = field(default_factory=time.time)


@dataclass(slots=True)
class StackState:
    processes: list[StackProcess] = field(default_factory=list)
    started_at: float = field(default_factory=time.time)
    log_dir: str | None = None
    infra_started: bool = False
    version: int = 1


@dataclass(frozen=True, slots=True)
class StackStatus:
    state: str
    running: list[StackProcess]
    dead: list[StackProcess]
    log_dir: str | None
    infra_started: bool


def load(path: Path = STACK_STATE_PATH) -> StackState | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        procs = [StackProcess(**p) for p in data.get("processes", [])]
        return StackState(
            processes=procs,
            started_at=data.get("started_at", time.time()),
            log_dir=data.get("log_dir"),
            infra_started=bool(data.get("infra_started", False)),
            version=int(data.get("version", 1)),
        )
    except Exception:
        return None


def save(state: StackState, path: Path = STACK_STATE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(state)
    # Convert command sequences to lists for JSON
    for proc in payload.get("processes", []):
        if isinstance(proc.get("command"), tuple):
            proc["command"] = list(proc["command"])
    tmp_fd, tmp_path = tempfile.mkstemp(prefix="stack.", suffix=".json", dir=path.parent)
    with os.fdopen(tmp_fd, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    os.replace(tmp_path, path)


def clear(path: Path = STACK_STATE_PATH) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        return


def is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        # Process exists but owned elsewhere; treat as alive to avoid killing foreign PIDs.
        return True


def status(state: StackState | None) -> StackStatus:
    if state is None or not state.processes:
        return StackStatus(
            state="stopped",
            running=[],
            dead=[],
            log_dir=None,
            infra_started=False,
        )
    running: list[StackProcess] = []
    dead: list[StackProcess] = []
    for proc in state.processes:
        (running if is_alive(proc.pid) else dead).append(proc)
    overall = "running" if running and not dead else ("degraded" if running else "stopped")
    return StackStatus(
        state=overall,
        running=running,
        dead=dead,
        log_dir=state.log_dir,
        infra_started=state.infra_started,
    )


def stop_processes(state: StackState, *, grace_seconds: float = 5.0) -> None:
    """Attempt to terminate tracked processes politely, then force kill."""

    sigkill = getattr(signal, "SIGKILL", None)
    process_map = {proc.pid: proc for proc in state.processes}
    pids: Iterable[int] = process_map.keys()
    for pid in pids:
        proc = process_map.get(pid)
        if proc is None:
            continue
        if proc.isolated:
            _send_signal_group(proc, signal.SIGTERM)
        else:
            terminate_process_tree(pid, signal.SIGTERM)

    deadline = time.time() + grace_seconds
    remaining: set[int] = set(pids)
    while remaining and time.time() < deadline:
        remaining = {pid for pid in remaining if is_alive(pid)}
        if remaining:
            time.sleep(0.2)

    for pid in list(remaining):
        proc = process_map.get(pid)
        if proc is None:
            continue
        if proc.isolated:
            if sigkill is not None:
                _send_signal_group(proc, sigkill)
            else:
                # Windows lacks SIGKILL; fall back to a second SIGTERM
                _send_signal_group(proc, signal.SIGTERM)
        else:
            if sigkill is None:
                terminate_process_tree(pid, signal.SIGTERM)
            else:
                terminate_process_tree(pid, sigkill)


def _send_signal(pid: int, sig: int, *, prefer_group: bool = False) -> None:
    """Signal a process; prefer its process group when available."""

    try:
        if prefer_group and hasattr(os, "killpg"):
            try:
                pgid = os.getpgid(pid)
            except OSError:
                pgid = None
            if pgid is not None and pgid > 0:
                os.killpg(pgid, sig)
                return
        os.kill(pid, sig)
    except ProcessLookupError:
        return
    except PermissionError:
        return


def _send_signal_group(proc: StackProcess, sig: int) -> None:
    """Send a signal to a stored process group when available."""

    if proc.pgid and proc.pgid > 0 and hasattr(os, "killpg") and os.name != "nt":
        try:
            os.killpg(proc.pgid, sig)
            return
        except ProcessLookupError:
            return
        except PermissionError:
            pass
        except Exception:
            pass
    _send_signal(proc.pid, sig, prefer_group=False)


__all__ = [
    "STACK_STATE_PATH",
    "StackProcess",
    "StackState",
    "load",
    "save",
    "clear",
    "is_alive",
    "status",
    "stop_processes",
]
