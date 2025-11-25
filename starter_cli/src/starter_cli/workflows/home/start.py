from __future__ import annotations

import os
import signal
import subprocess
import threading
import time
import webbrowser
from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from starter_cli.adapters.io.console import console
from starter_cli.core import CLIContext
from starter_cli.core.constants import PROJECT_ROOT
from starter_cli.core.status_models import ProbeState
from starter_cli.workflows.home import stack_state
from starter_cli.workflows.home.probes.api import api_probe
from starter_cli.workflows.home.probes.frontend import frontend_probe
from starter_cli.workflows.home.probes.util import tcp_check


@dataclass(slots=True)
class LaunchResult:
    label: str
    command: Sequence[str]
    process: subprocess.Popen[Any] | None
    error: str | None = None
    log_tail: deque[str] = field(default_factory=lambda: deque(maxlen=50))
    log_path: Path | None = None


class StartRunner:
    def __init__(
        self,
        ctx: CLIContext,
        *,
        target: str,
        timeout: float,
        open_browser: bool,
        skip_infra: bool = False,
        detach: bool = False,
        force: bool = False,
        pidfile: Path | None = None,
        log_dir: Path | None = None,
    ) -> None:
        self.ctx = ctx
        self.target = target
        self.timeout = timeout
        self.open_browser = open_browser
        self.skip_infra = skip_infra
        self.detach = detach
        self.force = force
        self.pidfile = pidfile or stack_state.STACK_STATE_PATH
        self.log_dir = log_dir or PROJECT_ROOT / "var" / "log"
        self._launches: list[LaunchResult] = []
        self._stop_event = threading.Event()
        self._log_files: list[Any] = []
        self._infra_started = (self.target == "dev") and not self.skip_infra

    def run(self) -> int:
        self._install_signal_handlers()

        # Guard: prevent two stacks running concurrently unless forced.
        existing_state = stack_state.load(self.pidfile)
        existing_status = stack_state.status(existing_state) if existing_state else None
        if (
            self.detach
            and existing_status
            and existing_status.state == "running"
            and not self.force
        ):
            console.warn(
                "Stack already running (use --force to replace).",
                topic="start",
            )
            for proc in existing_status.running:
                console.info(f"- {proc.label} pid={proc.pid}")
            return 1
        if self.force and existing_state:
            console.warn(
                "--force set; stopping previously tracked stack before launch",
                topic="start",
            )
            if existing_status and existing_status.running:
                safe_state = stack_state.StackState(
                    processes=existing_status.running,
                    log_dir=existing_state.log_dir,
                    infra_started=existing_state.infra_started,
                )
                stack_state.stop_processes(safe_state)
            else:
                console.info("No running PIDs in prior state; skipping process stop", topic="start")
            stack_state.clear(self.pidfile)

        # Guard: ensure required ports are free.
        if not self._ports_available():
            return 1

        launches: list[LaunchResult] = []
        if self.target == "dev" and not self.skip_infra:
            launches.append(self._spawn("infra", ["just", "dev-up"]))
        if self.target in {"dev", "backend"}:
            launches.append(
                self._spawn(
                    "backend",
                    ["hatch", "run", "serve"],
                    cwd=PROJECT_ROOT,
                    env=self._backend_env(),
                )
            )
        if self.target in {"dev", "frontend"}:
            # Note: pnpm requires the filter flag before the script when not using -r.
            launches.append(
                self._spawn(
                    "frontend",
                    ["pnpm", "--filter", "web-app", "dev"],
                    cwd=PROJECT_ROOT / "web-app",
                    env=self._frontend_env(),
                )
            )

        failures = [launch for launch in launches if launch.error]
        if failures:
            for failure in failures:
                console.error(f"Failed to start {failure.label}: {failure.error}")
            self._cleanup_processes()
            return 1

        # Health waiters
        deadline = time.time() + (self.timeout or 120)
        api_ok = frontend_ok = False
        while time.time() < deadline:
            early_failure = self._poll_launch_failures()
            if early_failure:
                console.error(early_failure)
                self._dump_tail()
                self._cleanup_processes()
                return 1
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

        if self.detach:
            self._record_state()
            console.success("Stack is running in background (managed by CLI).")
            self._print_ready_urls()
            self._close_logs()
            return 0

        console.success("Stack is running. Press Ctrl+C to stop processes started by this command.")
        self._print_ready_urls()
        return self._wait_for_processes()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _spawn(
        self,
        label: str,
        command: Sequence[str],
        *,
        cwd: Path | None = None,
        env: dict[str, str] | None = None,
    ) -> LaunchResult:
        try:
            stdout_target: Any
            log_path: Path | None = None
            if self.detach:
                log_path, stdout_target = self._open_log(label)
            else:
                stdout_target = subprocess.PIPE
            proc = subprocess.Popen(
                command,
                cwd=cwd or PROJECT_ROOT,
                env=env,
                stdout=stdout_target,
                stderr=subprocess.STDOUT,
                text=not self.detach,
            )
            launch = LaunchResult(label=label, command=command, process=proc, log_path=log_path)
            self._launches.append(launch)
            console.info(f"Started {label} pid={proc.pid} cmd={' '.join(command)}")
            if not self.detach:
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
            if launch.log_tail:
                console.info(f"--- last {len(launch.log_tail)} lines from {launch.label} ---")
                for line in launch.log_tail:
                    console.info(line)
            elif launch.log_path and launch.log_path.exists():
                tail = (
                    launch.log_path.read_text(encoding="utf-8", errors="ignore").splitlines()[-20:]
                )
                if tail:
                    console.info(
                        f"--- last {len(tail)} lines from {launch.label} ({launch.log_path}) ---"
                    )
                    for line in tail:
                        console.info(line)

    def _poll_launch_failures(self) -> str | None:
        """Detect early exits during the health wait and fail fast."""

        for launch in list(self._launches):
            proc = launch.process
            if not proc:
                continue
            ret = proc.poll()
            if ret is None:
                continue
            # Allow infra (docker compose) to exit 0 after bootstrapping.
            if launch.label == "infra" and ret == 0:
                console.info("infra completed successfully; continuing supervision")
                self._launches.remove(launch)
                continue
            if ret == 0:
                return f"{launch.label} exited early (code 0); stopping remaining processes."
            return f"{launch.label} exited with code {ret}; stopping remaining processes."
        return None

    def _wait_for_processes(self) -> int:
        """Block until stop requested or a managed process exits."""

        try:
            while not self._stop_event.is_set():
                for launch in list(self._launches):
                    proc = launch.process
                    if proc and proc.poll() is not None:
                        # Allow transient infra/bootstrap commands (e.g., just dev-up)
                        # to exit cleanly
                        if launch.label == "infra" and proc.returncode == 0:
                            console.info("infra completed successfully; continuing supervision")
                            self._launches.remove(launch)
                            continue

                        if proc.returncode == 0:
                            console.error(
                                f"{launch.label} exited unexpectedly with code 0; shutting down."
                            )
                            self._dump_tail()
                            self._cleanup_processes()
                            return 1

                        console.error(
                            f"{launch.label} exited with code {proc.returncode}; shutting down."
                        )
                        self._dump_tail()
                        self._cleanup_processes()
                        return proc.returncode or 1
                time.sleep(0.5)
        except KeyboardInterrupt:
            console.warn("Interrupted; cleaning up processes...")
        self._cleanup_processes()
        return 0

    def _print_ready_urls(self) -> None:
        """Surface ready endpoints once the stack is healthy."""

        import os

        api_url = os.getenv("API_BASE_URL", "http://localhost:8000")
        app_url = os.getenv("APP_PUBLIC_URL", "http://localhost:3000")
        console.info(f"Backend: {api_url}")
        console.info(f"Frontend: {app_url}")

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
        self._close_logs()

    def _install_signal_handlers(self) -> None:
        def _handler(signum, frame):
            console.warn(f"Received signal {signum}; cleaning up started processes...")
            self._stop_event.set()

        signal.signal(signal.SIGINT, _handler)
        signal.signal(signal.SIGTERM, _handler)

    # ------------------------------------------------------------------
    # Detached + port guard helpers
    # ------------------------------------------------------------------
    def _open_log(self, label: str) -> tuple[Path, Any]:
        self.log_dir.mkdir(parents=True, exist_ok=True)
        path = self.log_dir / f"{label}.log"
        self._rotate_log(path)
        # append to keep previous runs; rotation keeps size bounded
        fh = open(path, "a", buffering=1, encoding="utf-8")
        self._log_files.append(fh)
        return path, fh

    def _rotate_log(self, path: Path, *, max_bytes: int = 5_000_000, keep: int = 3) -> None:
        try:
            if not path.exists() or path.stat().st_size < max_bytes:
                return
        except OSError:
            return

        for idx in range(keep - 1, -1, -1):
            src = path if idx == 0 else path.with_name(f"{path.name}.{idx}")
            dest = path.with_name(f"{path.name}.{idx + 1}")
            if src.exists():
                try:
                    os.replace(src, dest)
                except OSError:
                    continue

    def _close_logs(self) -> None:
        for fh in self._log_files:
            try:
                fh.close()
            except Exception:
                continue
        self._log_files.clear()

    def _record_state(self) -> None:
        procs = [
            stack_state.StackProcess(
                label=launch.label,
                pid=int(launch.process.pid) if launch.process else -1,
                command=list(launch.command),
                log_path=str(launch.log_path) if launch.log_path else None,
            )
            for launch in self._launches
            if launch.process and launch.process.poll() is None
        ]
        state = stack_state.StackState(
            processes=procs,
            log_dir=str(self.log_dir),
            infra_started=self._infra_started,
        )
        stack_state.save(state, self.pidfile)
        console.info(f"Recorded stack state to {self.pidfile}")

    def _ports_available(self) -> bool:
        checks: list[tuple[str, str, int]] = []
        if self.target in {"dev", "backend"}:
            host, port = _parse_host_port(self._api_base_url(), default_port=8000)
            checks.append(("api", host, port))
        if self.target in {"dev", "frontend"}:
            # Next.js binds locally; guard the local port even when APP_PUBLIC_URL is remote
            port = self._frontend_listen_port()
            checks.append(("frontend", "127.0.0.1", port))

        busy: list[str] = []
        for label, host, port in checks:
            ok, detail = tcp_check(host, port, timeout=0.5)
            if ok:
                busy.append(f"{label} {host}:{port} ({detail})")

        if busy:
            message = "Ports already in use: " + ", ".join(busy)
            message += ". Stop existing services or use --force if they were started by this CLI."
            console.error(message, topic="start")
            return False
        return True

    # ------------------------------------------------------------------
    # Environment overlays per process
    # ------------------------------------------------------------------
    def _backend_env(self) -> dict[str, str]:
        env = os.environ.copy()
        env.pop("PORT", None)  # avoid inheriting frontend port for uvicorn
        env.setdefault("ALEMBIC_CONFIG", str(PROJECT_ROOT / "api-service" / "alembic.ini"))
        env.setdefault("ALEMBIC_SCRIPT_LOCATION", str(PROJECT_ROOT / "api-service" / "alembic"))
        return env

    def _frontend_env(self) -> dict[str, str]:
        env = os.environ.copy()
        port = self._frontend_listen_port()
        env["PORT"] = str(port)
        env.setdefault("APP_PUBLIC_URL", "http://localhost:3000")
        return env

    def _frontend_listen_port(self) -> int:
        host, url_port = _parse_host_port(self._app_public_url(), default_port=3000)
        if _is_local_host(host):
            return url_port

        env_port = os.getenv("PORT")
        if env_port and env_port.isdigit():
            return int(env_port)

        return 3000

    def _api_base_url(self) -> str:
        return os.getenv("API_BASE_URL") or "http://localhost:8000"

    def _app_public_url(self) -> str:
        return os.getenv("APP_PUBLIC_URL") or "http://localhost:3000"


def _parse_host_port(url: str, *, default_port: int) -> tuple[str, int]:
    from urllib.parse import urlparse

    parsed = urlparse(url)
    host = parsed.hostname or "localhost"
    port = parsed.port or default_port
    return host, port


def _is_local_host(host: str) -> bool:
    return host in {"localhost", "127.0.0.1", "::1"} or host.endswith(".local")


__all__ = ["LaunchResult", "StartRunner"]
