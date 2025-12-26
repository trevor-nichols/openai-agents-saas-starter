from __future__ import annotations

from starter_console.core.status_models import ProbeResult, ProbeState
from starter_console.workflows.home import stack_state


def stack_probe() -> ProbeResult:
    state = stack_state.load()
    if state is None:
        return ProbeResult(
            name="stack",
            state=ProbeState.SKIPPED,
            detail="not started",
            metadata={"state": "stopped"},
        )

    summary = stack_state.status(state)
    running = summary.running
    dead = summary.dead
    label = summary.state
    probe_state = (
        ProbeState.OK if label == "running" else ProbeState.WARN if running else ProbeState.ERROR
    )
    detail = f"{label} (running={len(running)} dead={len(dead)})"

    metadata = {
        "state": label,
        "running": [proc.pid for proc in running],
        "dead": [proc.pid for proc in dead],
        "log_dir": summary.log_dir,
        "infra_started": summary.infra_started,
    }

    return ProbeResult(
        name="stack",
        state=probe_state,
        detail=detail,
        metadata=metadata,
    )


__all__ = ["stack_probe"]
