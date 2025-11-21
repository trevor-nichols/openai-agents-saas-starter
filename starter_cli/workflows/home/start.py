from __future__ import annotations

import signal
import subprocess
import threading
import time
import webbrowser
from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from starter_cli.adapters.io.console import console
from starter_cli.core import CLIContext
from starter_cli.core.constants import PROJECT_ROOT
from starter_cli.core.status_models import ProbeState
from starter_cli.workflows.home.probes.api import api_probe
from starter_cli.workflows.home.probes.frontend import frontend_probe


@dataclass(slots=True)
class LaunchResult:
    label: str
    command: Sequence[str]
    process: subprocess.Popen[Any] | None
    error: str | None = None
    log_tail: deque[str] = field(default_factory=lambda: deque(maxlen=50))


class StartRunner:
    def __init__(
        self,
        ctx: CLIContext,
        *,
        target: str,
        timeout: float,
        open_browser: bool,
        skip_infra: bool = False,
    ) -> None:
        self.ctx = ctx
        self.target = target
        self.timeout = timeout
        self.open_browser = open_browser
        self.skip_infra = skip_infra
        self._launches: list[LaunchResult] = []
        self._stop_event = threading.Event()

    def run(self) -> int:
        self._install_signal_handlers()

        launches: list[LaunchResult] = []
        if self.target == "dev" and not self.skip_infra:
            launches.append(self._spawn("infra", ["just", "dev-up"]))
        if self.target in {"dev", "backend"}:
            launches.append(self._spawn("backend", ["hatch", "run", "serve"]))
        if self.target in {"dev", "frontend"}:
            launches.append(self._spawn("frontend", ["pnpm", "dev", "--filter", "web-app"]))

        failures = [launch for launch in launches if launch.error]
        if failures:
            for failure in failures:
                console.error(f"Failed to start {failure.label}: {failure.error}")
            return 1

        # Health waiters
        deadline = time.time() + (self.timeout or 120)
        api_ok = frontend_ok = False
        while time.time() < deadline:
            api_ok = (
                api_probe().state is ProbeState.OK if self.target in {"dev", "backend"} else True
            )
            frontend_ok = (
                frontend_probe().state is ProbeState.OK
                if self.target in {"dev", "frontend"}
                else True
            )
            if api_ok and frontend_ok:
                break
            time.sleep(1)

        console.info(
            "Health check: api="
            f"{'ok' if api_ok else 'down'} "
            f"frontend={'ok' if frontend_ok else 'down'}"
        )

        if not (api_ok and frontend_ok):
            self._dump_tail()

        if self.open_browser and frontend_ok:
            self._open_browser()

        code = 0 if api_ok and frontend_ok else 1
        if code != 0:
            console.error("Start failed; see above logs and remediation.")
            self._cleanup_processes()
            return code

        console.success("Stack is running. Press Ctrl+C to stop processes started by this command.")
        return self._wait_for_processes()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _spawn(self, label: str, command: Sequence[str]) -> LaunchResult:
        try:
            proc = subprocess.Popen(
                command,
                cwd=PROJECT_ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            launch = LaunchResult(label=label, command=command, process=proc)
            self._launches.append(launch)
            console.info(f"Started {label} pid={proc.pid} cmd={' '.join(command)}")
            self._start_log_thread(launch)
            return launch
        except FileNotFoundError as exc:
            return LaunchResult(label=label, command=command, process=None, error=str(exc))
        except Exception as exc:  # pragma: no cover - defensive
            return LaunchResult(label=label, command=command, process=None, error=str(exc))

    def _start_log_thread(self, launch: LaunchResult) -> None:
        if launch.process is None or launch.process.stdout is None:
            return

        def _consume() -> None:
            assert launch.process and launch.process.stdout
            for line in launch.process.stdout:
                if self._stop_event.is_set():
                    break
                line = line.rstrip()
                if line:
                    launch.log_tail.append(f"{launch.label}: {line}")
                    console.info(f"{launch.label}> {line}")

        threading.Thread(target=_consume, daemon=True).start()

    def _open_browser(self) -> None:
        # Use APP_PUBLIC_URL when present
        import os

        url = os.getenv("APP_PUBLIC_URL", "http://localhost:3000")
        try:
            webbrowser.open(url)
            console.success(f"Opened browser at {url}")
        except Exception as exc:  # pragma: no cover - defensive
            console.warn(f"Failed to open browser: {exc}")

    def _dump_tail(self) -> None:
        for launch in self._launches:
            if not launch.log_tail:
                continue
            console.info(f"--- last {len(launch.log_tail)} lines from {launch.label} ---")
            for line in launch.log_tail:
                console.info(line)

    def _wait_for_processes(self) -> int:
        """Block until stop requested or a managed process exits."""

        try:
            while not self._stop_event.is_set():
                for launch in self._launches:
                    proc = launch.process
                    if proc and proc.poll() is not None:
                        console.error(
                            f"{launch.label} exited with code {proc.returncode}; shutting down."
                        )
                        self._dump_tail()
                        self._cleanup_processes()
                        return 1
                time.sleep(0.5)
        except KeyboardInterrupt:
            console.warn("Interrupted; cleaning up processes...")
        self._cleanup_processes()
        return 0

    def _cleanup_processes(self) -> None:
        self._stop_event.set()
        for launch in self._launches:
            proc = launch.process
            if not proc:
                continue
            if proc.poll() is None:
                try:
                    proc.terminate()
                except Exception:  # pragma: no cover - defensive
                    pass
        # Give them a beat to exit
        time.sleep(0.2)
        for launch in self._launches:
            proc = launch.process
            if proc and proc.poll() is None:
                try:
                    proc.kill()
                except Exception:
                    pass

    def _install_signal_handlers(self) -> None:
        def _handler(signum, frame):
            console.warn(f"Received signal {signum}; cleaning up started processes...")
            self._stop_event.set()

        signal.signal(signal.SIGINT, _handler)
        signal.signal(signal.SIGTERM, _handler)


__all__ = ["LaunchResult", "StartRunner"]
