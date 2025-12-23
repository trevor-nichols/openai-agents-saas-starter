from __future__ import annotations

import atexit
import datetime
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

from starter_cli.core import CLIContext
from starter_cli.core.constants import PROJECT_ROOT
from starter_cli.core.status_models import ProbeState
from starter_cli.workflows.home import stack_state
from starter_cli.workflows.home.probes.api import api_probe
from starter_cli.workflows.home.probes.frontend import frontend_probe
from starter_cli.workflows.home.probes.util import tcp_check

TODAY = datetime.date.today().isoformat()


@dataclass(slots=True)
class LaunchResult:
    label: str
    command: Sequence[str]
    process: subprocess.Popen[Any] | None
    isolated: bool = False
    pgid: int | None = None
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
        self.console = ctx.console
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
        self._base_log_root, self.log_dir = self._resolve_log_dir(log_dir)

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
                        "No running PIDs in prior state; skipping process stop", topic="start"
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
                self._close_logs()
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
                log_path, stdout_target = self._open_log(label)
            else:
                stdout_target = subprocess.PIPE
            start_opts = self._subprocess_start_opts()
            proc = subprocess.Popen(
                command,
                cwd=cwd or PROJECT_ROOT,
                env=env,
                stdout=stdout_target,
                stderr=subprocess.STDOUT,
                text=not self.detach,
                **start_opts,
            )
            pgid = None
            if start_opts and hasattr(os, "getpgid"):
                try:
                    pgid = os.getpgid(proc.pid)
                except OSError:
                    pgid = None

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
                    self.console.info(f"{launch.label}> {line}")

        threading.Thread(target=_consume, daemon=True).start()

    def _open_browser(self) -> None:
        # Use APP_PUBLIC_URL when present
        import os

        url = os.getenv("APP_PUBLIC_URL", "http://localhost:3000")
        try:
            webbrowser.open(url)
            self.console.success(f"Opened browser at {url}")
        except Exception as exc:  # pragma: no cover - defensive
            self.console.warn(f"Failed to open browser: {exc}")

    def _dump_tail(self) -> None:
        for launch in self._launches:
            if launch.log_tail:
                self.console.info(f"--- last {len(launch.log_tail)} lines from {launch.label} ---")
                for line in launch.log_tail:
                    self.console.info(line)
            elif launch.log_path and launch.log_path.exists():
                tail = (
                    launch.log_path.read_text(encoding="utf-8", errors="ignore").splitlines()[-20:]
                )
                if tail:
                    self.console.info(
                        f"--- last {len(tail)} lines from {launch.label} ({launch.log_path}) ---"
                    )
                    for line in tail:
                        self.console.info(line)

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

        import os

        api_url = os.getenv("API_BASE_URL", "http://localhost:8000")
        app_url = os.getenv("APP_PUBLIC_URL", "http://localhost:3000")
        self.console.info(f"Backend: {api_url}")
        self.console.info(f"Frontend: {app_url}")

    def _cleanup_processes(self) -> None:
        self._stop_event.set()
        for launch in self._launches:
            self._terminate_launch(launch, force=False)

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
                self._terminate_launch(launch, force=True)
        self._close_logs()

    def _terminate_launch(self, launch: LaunchResult, *, force: bool) -> None:
        """Best-effort teardown for a spawned process tree.

        Uses the recorded process group first (covers cases where the leader exited
        before cleanup), then falls back to the live Popen handle.
        """

        if launch.isolated:
            sig = signal.SIGKILL if force else signal.SIGTERM
        else:
            sig = signal.SIGKILL if force else signal.SIGINT

        if launch.isolated and launch.pgid and os.name != "nt":
            try:
                os.killpg(launch.pgid, sig)
                return
            except ProcessLookupError:
                # Group already gone; nothing to do.
                return
            except PermissionError:
                # Fallback to per-process termination below.
                pass
            except Exception:
                pass

        proc = launch.process
        if proc is None:
            return
        # If the leader already exited, we may still have live children under the
        # same pgid. When pgid is missing (Windows or earlier failure), send the
        # signal to the leader pid as a last resort.
        if proc.poll() is None:
            if launch.isolated:
                self._terminate_process(proc, force=force)
            else:
                self._terminate_process_tree(proc.pid, sig)
            return
        if launch.isolated and os.name != "nt":
            try:
                pgid = os.getpgid(proc.pid)
            except OSError:
                return
            try:
                os.killpg(pgid, sig)
            except Exception:
                return

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
        self.console.info(f"Recorded stack state to {self.pidfile}")

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
            self.console.error(message, topic="start")
            return False
        return True

    # ------------------------------------------------------------------
    # Environment overlays per process
    # ------------------------------------------------------------------
    def _backend_env(self) -> dict[str, str]:
        env = os.environ.copy()
        env.pop("PORT", None)  # avoid inheriting frontend port for uvicorn
        env["LOG_ROOT"] = str(self._base_log_root)
        env.setdefault(
            "ALEMBIC_CONFIG",
            str(PROJECT_ROOT / "apps" / "api-service" / "alembic.ini"),
        )
        env.setdefault(
            "ALEMBIC_SCRIPT_LOCATION",
            str(PROJECT_ROOT / "apps" / "api-service" / "alembic"),
        )
        return env

    def _frontend_env(self) -> dict[str, str]:
        env = os.environ.copy()
        port = self._frontend_listen_port()
        env["PORT"] = str(port)
        env.setdefault("APP_PUBLIC_URL", "http://localhost:3000")
        env["LOG_ROOT"] = str(self._base_log_root)
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

    # ------------------------------------------------------------------
    # Logging helpers
    # ------------------------------------------------------------------
    def _resolve_log_dir(self, configured: Path | None) -> tuple[Path, Path]:
        """
        Resolve the daily log root and CLI log directory.

        - base_root: LOG_ROOT env or project var/log
        - date_root: base_root/YYYY-MM-DD
        - cli_root: date_root/cli
        """

        env_root = os.getenv("LOG_ROOT")
        base_root_raw = Path(env_root).expanduser() if env_root else (PROJECT_ROOT / "var" / "log")
        if configured:
            base_root_raw = configured
        base_root = base_root_raw if base_root_raw.is_absolute() else (PROJECT_ROOT / base_root_raw)
        date_root = base_root / TODAY
        cli_root = date_root / "cli"
        try:
            base_root.mkdir(parents=True, exist_ok=True)
            date_root.mkdir(parents=True, exist_ok=True)
            cli_root.mkdir(parents=True, exist_ok=True)
            current_link = base_root / "current"
            if current_link.exists() or current_link.is_symlink():
                current_link.unlink()
            current_link.symlink_to(date_root, target_is_directory=True)
        except OSError:
            # Non-fatal; fall back to base_root when symlink fails
            cli_root = base_root
        return base_root, cli_root

    def _subprocess_start_opts(self) -> dict[str, Any]:
        """
        In detached mode, ensure each child becomes its own process group so the
        CLI can stop it later via recorded PIDs without relying on the terminal
        foreground process group.

        In foreground mode, keep children attached to the terminal process group
        so Ctrl+C reliably reaches the dev servers even if intermediate wrappers
        (just/hatch) terminate quickly.
        """

        if not self.detach:
            return {}
        if os.name == "nt":
            return {"creationflags": getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)}
        return {"start_new_session": True}

    def _terminate_process(self, proc: subprocess.Popen[Any], *, force: bool) -> None:
        """
        Terminate a process and its process group to avoid orphaned children
        (e.g., Next.js dev server continuing after pnpm is killed).
        """

        try:
            if os.name == "nt":
                # CTRL_BREAK reaches the new process group created above
                ctrl_break = getattr(signal, "CTRL_BREAK_EVENT", signal.SIGTERM)
                sig = ctrl_break if not force else signal.SIGTERM
                proc.send_signal(sig)
            else:
                sig = signal.SIGKILL if force else signal.SIGTERM
                os.killpg(proc.pid, sig)
        except ProcessLookupError:
            return
        except Exception:
            try:
                proc.kill() if force else proc.terminate()
            except Exception:
                pass

    def _terminate_process_tree(self, root_pid: int, sig: int) -> None:
        """
        Best-effort process-tree teardown (POSIX + Windows).

        Foreground mode intentionally avoids creating new sessions/process groups
        so Ctrl+C can reach children. When we need to stop early (health failure,
        error, etc.), we fall back to killing the spawned process tree by PID.
        """

        if root_pid <= 0:
            return

        if os.name == "nt":
            # /T terminates the child process tree; /F forces.
            cmd = ["taskkill", "/PID", str(root_pid), "/T"]
            if sig == getattr(signal, "SIGKILL", None):
                cmd.append("/F")
            try:
                subprocess.run(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
            except Exception:
                return
            return

        pids = _collect_descendant_pids(root_pid)
        for pid in pids:
            try:
                os.kill(pid, sig)
            except ProcessLookupError:
                continue
            except PermissionError:
                continue
            except Exception:
                continue


def _parse_host_port(url: str, *, default_port: int) -> tuple[str, int]:
    from urllib.parse import urlparse

    parsed = urlparse(url)
    host = parsed.hostname or "localhost"
    port = parsed.port or default_port
    return host, port


def _is_local_host(host: str) -> bool:
    if host in {"localhost", "::1", "0.0.0.0"}:
        return True
    # IPv4 loopback range (RFC 1122) is 127.0.0.0/8, not just 127.0.0.1.
    if host.startswith("127."):
        return True
    return host.endswith(".local")


def _collect_descendant_pids(root_pid: int) -> list[int]:
    """
    Return a post-order list of PIDs: children first, then root.

    Uses `ps` to avoid adding runtime dependencies (psutil) to the CLI.
    """

    try:
        result = subprocess.run(
            ["ps", "-Ao", "pid=,ppid="],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except Exception:
        return [root_pid]

    children_by_ppid: dict[int, list[int]] = {}
    for line in result.stdout.splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) != 2:
            continue
        try:
            pid = int(parts[0])
            ppid = int(parts[1])
        except ValueError:
            continue
        children_by_ppid.setdefault(ppid, []).append(pid)

    order: list[int] = []
    stack: list[int] = [root_pid]
    seen: set[int] = set()
    while stack:
        pid = stack.pop()
        if pid in seen:
            continue
        seen.add(pid)
        order.append(pid)
        stack.extend(children_by_ppid.get(pid, ()))

    # Reverse pre-order => children before parents.
    return list(reversed(order))


__all__ = ["LaunchResult", "StartRunner"]
