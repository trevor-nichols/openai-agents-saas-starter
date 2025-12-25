from __future__ import annotations

import atexit
import os
import signal
import subprocess
import threading
import time
import webbrowser
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from starter_console.core import CLIContext
from starter_console.core.constants import PROJECT_ROOT
from starter_console.core.status_models import ProbeState
from starter_console.workflows.home import stack_state
from starter_console.workflows.home.probes.api import api_probe
from starter_console.workflows.home.probes.frontend import frontend_probe
from starter_console.workflows.home.probes.util import tcp_check

from . import env as env_utils
from .logs import LogSession
from .models import LaunchResult
from .processes import resolve_pgid, subprocess_start_opts, terminate_launch


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
        self.console = ctx.console
        self.target = target
        self.timeout = timeout
        self.open_browser = open_browser
        self.skip_infra = skip_infra
        self.detach = detach
        self.force = force
        self.pidfile = pidfile or stack_state.STACK_STATE_PATH
        self._launches: list[LaunchResult] = []
        self._stop_event = threading.Event()
        self._infra_started = (self.target == "dev") and not self.skip_infra
        self._logs = LogSession(
            project_root=PROJECT_ROOT,
            env=os.environ,
            override=log_dir,
        )
        self._base_log_root = self._logs.base_log_root
        self.log_dir = self._logs.log_dir

    def run(self) -> int:
        self._install_signal_handlers()
        self._install_exit_handler()

        try:
            # Guard: prevent two stacks running concurrently unless forced.
            existing_state = stack_state.load(self.pidfile)
            existing_status = stack_state.status(existing_state) if existing_state else None
            if (
                self.detach
                and existing_status
                and existing_status.state == "running"
                and not self.force
            ):
                self.console.warn(
                    "Stack already running (use --force to replace).",
                    topic="start",
                )
                for proc in existing_status.running:
                    self.console.info(f"- {proc.label} pid={proc.pid}")
                return 1
            if self.force and existing_state:
                self.console.warn(
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
                    self.console.info(
                        "No running PIDs in prior state; skipping process stop",
                        topic="start",
                    )
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
                        cwd=PROJECT_ROOT / "apps" / "api-service",
                        env=self._backend_env(),
                    )
                )
            if self.target in {"dev", "frontend"}:
                launches.append(
                    self._spawn(
                        "frontend",
                        ["pnpm", "dev", "--webpack"],
                        cwd=PROJECT_ROOT / "apps" / "web-app",
                        env=self._frontend_env(),
                    )
                )

            failures = [launch for launch in launches if launch.error]
            if failures:
                for failure in failures:
                    self.console.error(f"Failed to start {failure.label}: {failure.error}")
                self._cleanup_processes()
                return 1

            # Health waiters
            deadline = time.time() + (self.timeout or 120)
            api_ok = frontend_ok = False
            while time.time() < deadline:
                if self._stop_event.is_set():
                    self.console.warn("Stop requested; cleaning up processes...", topic="start")
                    self._cleanup_processes()
                    return 0
                early_failure = self._poll_launch_failures()
                if early_failure:
                    self.console.error(early_failure)
                    self._dump_tail()
                    self._cleanup_processes()
                    return 1
                api_ok = (
                    api_probe().state is ProbeState.OK
                    if self.target in {"dev", "backend"}
                    else True
                )
                frontend_ok = (
                    frontend_probe().state is ProbeState.OK
                    if self.target in {"dev", "frontend"}
                    else True
                )
                if api_ok and frontend_ok:
                    break
                try:
                    time.sleep(1)
                except InterruptedError:
                    raise KeyboardInterrupt from None

            self.console.info(
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
                self.console.error("Start failed; see above logs and remediation.")
                self._cleanup_processes()
                return code

            if self.detach:
                self._record_state()
                self.console.success("Stack is running in background (managed by CLI).")
                self._print_ready_urls()
                self._logs.close()
                return 0

            self.console.success(
                "Stack is running. Press Ctrl+C to stop processes started by this command."
            )
            self._print_ready_urls()
            return self._wait_for_processes()
        except KeyboardInterrupt:
            self.console.warn("Interrupted; cleaning up processes...", topic="start")
            self._cleanup_processes()
            return 0
        except Exception:
            # Defensive: never leave children orphaned
            self._cleanup_processes()
            raise

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
                log_path, stdout_target = self._logs.open_log(label)
            else:
                stdout_target = subprocess.PIPE
            start_opts = subprocess_start_opts(self.detach)
            proc = subprocess.Popen(
                command,
                cwd=cwd or PROJECT_ROOT,
                env=env,
                stdout=stdout_target,
                stderr=subprocess.STDOUT,
                text=not self.detach,
                **start_opts,
            )
            pgid = resolve_pgid(proc, start_opts)

            launch = LaunchResult(
                label=label,
                command=command,
                process=proc,
                isolated=bool(start_opts),
                pgid=pgid,
                log_path=log_path,
            )
            self._launches.append(launch)
            self.console.info(f"Started {label} pid={proc.pid} cmd={' '.join(command)}")
            if not self.detach:
                self._logs.start_log_thread(launch, self.console, self._stop_event)
            return launch
        except FileNotFoundError as exc:
            return LaunchResult(label=label, command=command, process=None, error=str(exc))
        except Exception as exc:  # pragma: no cover - defensive
            return LaunchResult(label=label, command=command, process=None, error=str(exc))

    def _open_browser(self) -> None:
        # Use APP_PUBLIC_URL when present
        url = os.getenv("APP_PUBLIC_URL", env_utils.DEFAULT_APP_URL)
        try:
            webbrowser.open(url)
            self.console.success(f"Opened browser at {url}")
        except Exception as exc:  # pragma: no cover - defensive
            self.console.warn(f"Failed to open browser: {exc}")

    def _dump_tail(self) -> None:
        self._logs.dump_tail(self._launches, self.console)

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
                self.console.info("infra completed successfully; continuing supervision")
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
                            self.console.info(
                                "infra completed successfully; continuing supervision"
                            )
                            self._launches.remove(launch)
                            continue

                        if proc.returncode == 0:
                            self.console.error(
                                f"{launch.label} exited unexpectedly with code 0; shutting down."
                            )
                            self._dump_tail()
                            self._cleanup_processes()
                            return 1

                        self.console.error(
                            f"{launch.label} exited with code {proc.returncode}; shutting down."
                        )
                        self._dump_tail()
                        self._cleanup_processes()
                        return proc.returncode or 1
                time.sleep(0.5)
        except KeyboardInterrupt:
            self.console.warn("Interrupted; cleaning up processes...")
        self._cleanup_processes()
        return 0

    def _print_ready_urls(self) -> None:
        """Surface ready endpoints once the stack is healthy."""

        api_url = env_utils.api_base_url(os.environ)
        app_url = env_utils.app_public_url(os.environ)
        self.console.info(f"Backend: {api_url}")
        self.console.info(f"Frontend: {app_url}")

    def _cleanup_processes(self) -> None:
        self._stop_event.set()
        for launch in self._launches:
            terminate_launch(launch, force=False)

        deadline = time.time() + 2.0
        while time.time() < deadline:
            still_running = False
            for launch in self._launches:
                proc = launch.process
                if proc and proc.poll() is None:
                    still_running = True
                    break
            if not still_running:
                break
            time.sleep(0.1)

        for launch in self._launches:
            proc = launch.process
            if proc and proc.poll() is None:
                terminate_launch(launch, force=True)
        self._logs.close()

    def _install_signal_handlers(self) -> None:
        def _handler(signum, frame):
            self.console.warn(f"Received signal {signum}; cleaning up started processes...")
            self._stop_event.set()
            raise KeyboardInterrupt

        signal.signal(signal.SIGINT, _handler)
        signal.signal(signal.SIGTERM, _handler)

    def _install_exit_handler(self) -> None:
        if self.detach:
            return

        def _cleanup() -> None:
            if self._launches and not self._stop_event.is_set():
                self._cleanup_processes()

        atexit.register(_cleanup)

    # ------------------------------------------------------------------
    # Detached + port guard helpers
    # ------------------------------------------------------------------
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
        self.console.info(f"Recorded stack state to {self.pidfile}")

    def _ports_available(self) -> bool:
        checks: list[tuple[str, str, int]] = []
        if self.target in {"dev", "backend"}:
            host, port = env_utils.parse_host_port(
                env_utils.api_base_url(os.environ), default_port=8000
            )
            checks.append(("api", host, port))
        if self.target in {"dev", "frontend"}:
            # Next.js binds locally; guard the local port even when APP_PUBLIC_URL is remote
            port = env_utils.frontend_listen_port(os.environ)
            checks.append(("frontend", "127.0.0.1", port))

        busy: list[str] = []
        for label, host, port in checks:
            ok, detail = tcp_check(host, port, timeout=0.5)
            if ok:
                busy.append(f"{label} {host}:{port} ({detail})")

        if busy:
            message = "Ports already in use: " + ", ".join(busy)
            message += ". Stop existing services or use --force if they were started by this CLI."
            self.console.error(message, topic="start")
            return False
        return True

    # ------------------------------------------------------------------
    # Environment overlays per process
    # ------------------------------------------------------------------
    def _backend_env(self) -> dict[str, str]:
        return env_utils.build_backend_env(
            os.environ,
            project_root=PROJECT_ROOT,
            base_log_root=self._base_log_root,
        )

    def _frontend_env(self) -> dict[str, str]:
        return env_utils.build_frontend_env(
            os.environ,
            base_log_root=self._base_log_root,
        )


__all__ = ["StartRunner"]
