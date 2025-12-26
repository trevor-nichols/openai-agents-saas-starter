from __future__ import annotations

import os
import signal
import subprocess
from typing import Any

from ..process_utils import terminate_process_tree
from .models import LaunchResult


def subprocess_start_opts(detach: bool) -> dict[str, Any]:
    """
    In detached mode, ensure each child becomes its own process group so the
    CLI can stop it later via recorded PIDs without relying on the terminal
    foreground process group.

    In foreground mode, keep children attached to the terminal process group
    so Ctrl+C reliably reaches the dev servers even if intermediate wrappers
    (just/hatch) terminate quickly.
    """

    if not detach:
        return {}
    if os.name == "nt":
        return {"creationflags": getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)}
    return {"start_new_session": True}


def resolve_pgid(proc: subprocess.Popen[Any], start_opts: dict[str, Any]) -> int | None:
    if not start_opts or not hasattr(os, "getpgid"):
        return None
    try:
        return os.getpgid(proc.pid)
    except OSError:
        return None


def terminate_launch(launch: LaunchResult, *, force: bool) -> None:
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
            _terminate_process(proc, force=force)
        else:
            _terminate_process_tree(proc.pid, sig)
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


def _terminate_process(proc: subprocess.Popen[Any], *, force: bool) -> None:
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


def _terminate_process_tree(root_pid: int, sig: int) -> None:
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

    terminate_process_tree(root_pid, sig)


__all__ = ["resolve_pgid", "subprocess_start_opts", "terminate_launch"]
