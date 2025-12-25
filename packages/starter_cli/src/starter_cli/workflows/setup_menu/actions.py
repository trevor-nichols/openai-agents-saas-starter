from __future__ import annotations

from collections.abc import Callable

from starter_cli.core import CLIContext, CLIError
from starter_cli.workflows.setup.dev_user import (
    build_default_dev_user_config,
    seed_dev_user_with_context,
)

ActionRunner = Callable[[CLIContext], int]


def _run_dev_user(ctx: CLIContext) -> int:
    config = build_default_dev_user_config()
    status = seed_dev_user_with_context(ctx, config)
    if status not in {"created", "rotated", "exists"}:
        raise CLIError(f"Unexpected dev user seed result: {status}")
    return 0


ACTION_RUNNERS: dict[str, ActionRunner] = {
    "dev_user": _run_dev_user,
}


def run_setup_action(ctx: CLIContext, action_key: str) -> int:
    runner = ACTION_RUNNERS.get(action_key)
    if runner is None:
        raise CLIError(
            f"Setup action '{action_key}' must be run from its dedicated pane."
        )
    return runner(ctx)


__all__ = ["ACTION_RUNNERS", "ActionRunner", "run_setup_action"]
