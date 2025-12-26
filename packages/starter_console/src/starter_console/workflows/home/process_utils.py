from __future__ import annotations

import os
import signal
import subprocess


def collect_descendant_pids(root_pid: int) -> list[int]:
    """
    Return a post-order list of PIDs: children first, then root.

    Uses `ps` to avoid adding runtime dependencies (psutil) to the CLI.
    """

    if root_pid <= 0:
        return []

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


def terminate_process_tree(root_pid: int, sig: int) -> None:
    """
    Best-effort process-tree teardown (POSIX + Windows).

    Uses taskkill on Windows and `ps` walking on POSIX.
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

    for pid in collect_descendant_pids(root_pid):
        try:
            os.kill(pid, sig)
        except ProcessLookupError:
            continue
        except PermissionError:
            continue
        except Exception:
            continue


__all__ = ["collect_descendant_pids", "terminate_process_tree"]
