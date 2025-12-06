from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

from dotenv import dotenv_values

from starter_cli.adapters.io.console import console
from starter_cli.core import CLIContext
from starter_cli.core.constants import PROJECT_ROOT
from starter_cli.workflows.home import stack_state


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "stop",
        help="Stop services started by `start --detached` and clear tracked state.",
    )
    parser.add_argument(
        "--pidfile",
        type=Path,
        default=None,
        help="Path to stack state file (default var/run/stack.json).",
    )
    parser.set_defaults(handler=_handle_stop)


def _handle_stop(args: argparse.Namespace, ctx: CLIContext) -> int:
    pidfile = args.pidfile or stack_state.STACK_STATE_PATH
    state = stack_state.load(pidfile)
    if state is None or not state.processes:
        console.info("No CLI-managed stack found (nothing to stop).")
        stack_state.clear(pidfile)  # clear corrupted/empty files
        return 0

    current = stack_state.status(state)
    running = current.running
    dead = current.dead

    if running:
        console.info("Stopping managed processes…")
        stack_state.stop_processes(state)
    else:
        console.warn("Tracked processes are already stopped; clearing state.")

    if dead:
        for proc in dead:
            console.warn(
                "Process "
                f"{getattr(proc, 'label', '?')} pid={getattr(proc, 'pid', '?')} "
                "was not running."
            )

    if state.infra_started:
        _docker_compose_down()

    stack_state.clear(pidfile)
    console.success("Stack stopped and state cleared.")
    return 0


def _docker_compose_down() -> None:
    project_root = ctx_project_root()
    compose_file = project_root / "ops" / "compose" / "docker-compose.yml"
    if not compose_file.exists():
        console.warn(f"Compose file not found at {compose_file}; skipping docker compose down.")
        return
    try:
        console.info("Running docker compose down for project services…")
        compose_env = dotenv_values(project_root / ".env.compose")
        env = {k: v for k, v in compose_env.items() if v is not None}
        env.update(os.environ)  # allow runtime env to override compose defaults
        env.setdefault("COMPOSE_FILE", str(compose_file))
        subprocess.run(
            ["docker", "compose", "-f", str(compose_file), "down"],
            cwd=project_root,
            env=env,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        console.warn("docker not found; skip compose down.")
    except subprocess.CalledProcessError:
        console.warn("docker compose down failed (containers may still be running).")


def ctx_project_root() -> Path:
    """Return the project root (kept for test monkeypatching)."""

    return PROJECT_ROOT


__all__ = ["register", "ctx_project_root"]
