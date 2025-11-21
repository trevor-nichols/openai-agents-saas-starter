from __future__ import annotations

import subprocess
import sys
import time
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from starter_cli.adapters.io.console import console
from starter_cli.core import CLIContext
from starter_cli.core.constants import PROJECT_ROOT
from starter_cli.core.status_models import ProbeResult, ProbeState
from starter_cli.workflows.home.probes.api import api_probe
from starter_cli.workflows.home.probes.frontend import frontend_probe


@dataclass(slots=True)
class LaunchResult:
    label: str
    command: Sequence[str]
    process: subprocess.Popen[Any] | None
    error: str | None = None


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

    def run(self) -> int:
        launches: list[LaunchResult] = []
        if self.target == "dev" and not self.skip_infra:
            launches.append(self._spawn("infra", ["just", "dev-up"]))
        if self.target in {"dev", "backend"}:
            launches.append(self._spawn("backend", ["hatch", "run", "serve"]))
        if self.target in {"dev", "frontend"}:
            launches.append(self._spawn("frontend", ["pnpm", "dev", "--filter", "web-app"]))

        failures = [l for l in launches if l.error]
        if failures:
            for failure in failures:
                console.error(f"Failed to start {failure.label}: {failure.error}")
            return 1

        # Health waiters
        deadline = time.time() + (self.timeout or 120)
        api_ok = frontend_ok = False
        while time.time() < deadline:
            api_ok = api_probe().state is ProbeState.OK if self.target in {"dev", "backend"} else True
            frontend_ok = (
                frontend_probe().state is ProbeState.OK if self.target in {"dev", "frontend"} else True
            )
            if api_ok and frontend_ok:
                break
            time.sleep(1)

        console.info(
            f"Health check: api={'ok' if api_ok else 'down'} frontend={'ok' if frontend_ok else 'down'}"
        )

        if self.open_browser and frontend_ok:
            self._open_browser()

        return 0 if api_ok and frontend_ok else 1

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _spawn(self, label: str, command: Sequence[str]) -> LaunchResult:
        try:
            proc = subprocess.Popen(command, cwd=PROJECT_ROOT, stdout=sys.stdout, stderr=sys.stderr)
            console.info(f"Started {label} pid={proc.pid} cmd={' '.join(command)}")
            return LaunchResult(label=label, command=command, process=proc)
        except FileNotFoundError as exc:
            return LaunchResult(label=label, command=command, process=None, error=str(exc))
        except Exception as exc:  # pragma: no cover - defensive
            return LaunchResult(label=label, command=command, process=None, error=str(exc))

    def _open_browser(self) -> None:
        # Use APP_PUBLIC_URL when present
        import os

        url = os.getenv("APP_PUBLIC_URL", "http://localhost:3000")
        try:
            webbrowser.open(url)
            console.success(f"Opened browser at {url}")
        except Exception as exc:  # pragma: no cover - defensive
            console.warn(f"Failed to open browser: {exc}")


__all__ = ["StartRunner", "LaunchResult"]
