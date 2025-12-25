from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values

from starter_console.core import CLIContext
from starter_console.ports.console import ConsolePort
from starter_console.workflows.home import stack_state


@dataclass(frozen=True, slots=True)
class StopStackResult:
    stopped: bool
    had_dead: bool
    infra_stopped: bool


def stop_stack(ctx: CLIContext, *, pidfile: Path | None) -> StopStackResult:
    console = ctx.console
    pidfile = pidfile or stack_state.STACK_STATE_PATH
    state = stack_state.load(pidfile)
    if state is None or not state.processes:
        console.info("No CLI-managed stack found (nothing to stop).")
        stack_state.clear(pidfile)  # clear corrupted/empty files
        return StopStackResult(stopped=False, had_dead=False, infra_stopped=False)

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

    infra_stopped = False
    if state.infra_started:
        infra_stopped = _docker_compose_down(ctx, console)

    stack_state.clear(pidfile)
    console.success("Stack stopped and state cleared.")
    return StopStackResult(
        stopped=bool(running),
        had_dead=bool(dead),
        infra_stopped=infra_stopped,
    )


def _docker_compose_down(ctx: CLIContext, console: ConsolePort) -> bool:
    project_root = ctx.project_root
    compose_file = project_root / "ops" / "compose" / "docker-compose.yml"
    if not compose_file.exists():
        console.warn(f"Compose file not found at {compose_file}; skipping docker compose down.")
        return False
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
        return True
    except FileNotFoundError:
        console.warn("docker not found; skip compose down.")
        return False
    except subprocess.CalledProcessError:
        console.warn("docker compose down failed (containers may still be running).")
        return False


__all__ = ["StopStackResult", "stop_stack"]
