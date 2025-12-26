from __future__ import annotations

import time

from starter_console.core import CLIContext
from starter_console.ui.action_runner import ActionRunner


def test_action_runner_executes(tmp_path) -> None:
    ctx = CLIContext(project_root=tmp_path)
    output: list[str] = []
    status: list[str] = []
    completed: list[bool] = []

    def on_status(message: str) -> None:
        status.append(message)

    def on_output(message: str) -> None:
        output.append(message)

    def on_complete(_: object) -> None:
        completed.append(True)

    runner: ActionRunner[int] = ActionRunner(
        ctx=ctx,
        on_status=on_status,
        on_output=on_output,
        on_complete=on_complete,
    )

    def task(task_ctx: CLIContext) -> int:
        task_ctx.console.info("running", topic="test")
        return 0

    assert runner.start("Test", task) is True

    for _ in range(50):
        runner.refresh_output()
        if completed:
            break
        time.sleep(0.02)

    assert completed
    assert any("running" in line for line in output)
    assert any("Test" in line for line in status)
