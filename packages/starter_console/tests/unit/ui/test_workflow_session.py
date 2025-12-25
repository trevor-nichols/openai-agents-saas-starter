from __future__ import annotations

from pathlib import Path

from starter_console.core import CLIContext
from starter_console.ui.workflow_session import InteractiveWorkflowSession, WorkflowLog, WorkflowNotifyPort


def test_workflow_log_trims_tail() -> None:
    log = WorkflowLog(max_lines=3)
    log.append("line-1")
    log.append("line-2")
    log.append("line-3")
    log.append("line-4")
    assert log.snapshot() == ("line-2", "line-3", "line-4")


def test_workflow_notify_port_records_messages() -> None:
    log = WorkflowLog(max_lines=5)
    notify = WorkflowNotifyPort(log)
    notify.info("hello", topic="stripe")
    notify.warn("warned")
    lines = log.snapshot()
    assert any("[INFO][stripe] hello" in line for line in lines)
    assert any("[WARN] warned" in line for line in lines)


def test_interactive_workflow_session_records_result(tmp_path: Path) -> None:
    ctx = CLIContext(project_root=tmp_path)

    def runner(runner_ctx: CLIContext) -> str:
        runner_ctx.console.info("boot", topic="test")
        return "ok"

    session: InteractiveWorkflowSession[str] = InteractiveWorkflowSession(ctx, runner=runner)
    session.start()
    assert session.wait(timeout=2.0) is True
    assert session.result.error is None
    assert session.result.value == "ok"
    assert any("boot" in line for line in session.log.snapshot())
