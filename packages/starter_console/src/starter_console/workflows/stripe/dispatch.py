from __future__ import annotations

import json
import uuid
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from starter_console.core import CLIContext, CLIError
from starter_console.ports.console import ConsolePort
from starter_console.services.infra.backend_scripts import extract_json_payload, run_backend_script


@dataclass(slots=True)
class DispatchListConfig:
    handler: str
    status: str
    limit: int
    page: int


@dataclass(slots=True)
class DispatchReplayConfig:
    dispatch_ids: list[str] | None
    event_ids: list[str] | None
    status: str | None
    limit: int
    handler: str
    assume_yes: bool


def run_dispatch_list(ctx: CLIContext, config: DispatchListConfig) -> int:
    args = _build_list_args(config)
    payload = _run_backend_dispatch(ctx, args, required_keys=["dispatches"])
    dispatches = payload.get("dispatches", [])
    if not dispatches:
        ctx.console.info("No dispatches found.", topic="stripe")
        return 0

    page = int(payload.get("page") or config.page)
    limit = int(payload.get("limit") or config.limit)
    ctx.console.info(f"Page {page} (limit {limit})", topic="stripe")
    for item in dispatches:
        ctx.console.print(_format_dispatch_row(item))
    return 0


def run_dispatch_replay(ctx: CLIContext, config: DispatchReplayConfig) -> int:
    if not config.dispatch_ids and not config.event_ids and not config.status:
        raise CLIError("Provide --dispatch-id, --event-id, or --status for replay.")

    if ctx.presenter is None:  # pragma: no cover - defensive
        raise CLIError("Presenter not initialized.")
    prompt = ctx.presenter.prompt

    targets = _preview_replay_targets(ctx, config)
    if not targets:
        ctx.console.info("No dispatches to replay.", topic="stripe")
        return 0

    if not config.assume_yes and not _confirm_replay(ctx.console, targets, prompt):
        ctx.console.info("Replay aborted by user.", topic="stripe")
        return 0

    payload = _run_backend_dispatch(
        ctx,
        _build_replay_args(config, preview=False),
        required_keys=["replayed", "errors"],
    )
    for item in payload.get("replayed", []):
        ctx.console.success(
            f"Replayed dispatch {item.get('id')} (processed_at={item.get('processed_at')})",
            topic="stripe",
        )
    for item in payload.get("errors", []):
        ctx.console.error(
            f"Failed to replay {item.get('id')}: {item.get('error')}",
            topic="stripe",
        )
    return 0


def run_dispatch_validate_fixtures(ctx: CLIContext, path: str) -> int:
    console = ctx.console
    directory = Path(path)
    if not directory.is_absolute():
        directory = (ctx.project_root / directory).resolve()
    if not directory.exists():
        raise CLIError(f"Fixture directory '{directory}' not found.")
    failures = 0
    for file in sorted(directory.glob("*.json")):
        try:
            json.loads(file.read_text(encoding="utf-8"))
            console.success(f"{file.relative_to(directory)}", topic="stripe-fixtures")
        except json.JSONDecodeError as exc:
            failures += 1
            console.error(f"{file}: invalid JSON ({exc})", topic="stripe-fixtures")
    if failures:
        raise CLIError(f"Fixture validation failed ({failures} files).")
    return 0


async def replay_dispatches_with_repo(
    repo: Any,
    *,
    dispatch_ids: list[str] | None,
    event_ids: list[str] | None,
    status: str | None,
    limit: int,
    handler: str,
    assume_yes: bool,
    console: ConsolePort,
    dispatcher: Any | None,
    billing: Any | None,
    confirm: Callable[[list[uuid.UUID]], bool] | None = None,
) -> Any:
    if dispatcher is None or billing is None:
        raise CLIError("Stripe dispatcher or billing service unavailable.")

    dispatcher.configure(repository=repo, billing=billing)

    targets: list[uuid.UUID] = []
    if dispatch_ids:
        targets.extend(uuid.UUID(value) for value in dispatch_ids)
    elif event_ids:
        for event_id in event_ids:
            event = await repo.get_by_event_id(event_id)
            if event is None:
                console.warn(f"Event {event_id} not found; skipping.", topic="stripe")
                continue
            dispatch = await repo.ensure_dispatch(event_id=event.id, handler=handler)
            targets.append(dispatch.id)
    elif status:
        rows = await repo.list_dispatches(handler=handler, status=status, limit=limit)
        targets.extend(row[0].id for row in rows)
    else:
        raise CLIError("Provide --dispatch-id, --event-id, or --status for replay.")

    if not targets:
        console.info("No dispatches to replay.", topic="stripe")
        return 0

    confirmation = confirm or (lambda ids: _confirm_replay(console, [str(t) for t in ids]))
    if not assume_yes and not confirmation(targets):
        console.info("Replay aborted by user.", topic="stripe")
        return 0

    for dispatch_id in targets:
        try:
            result = await dispatcher.replay_dispatch(dispatch_id)
            when = result.processed_at.isoformat() if result.processed_at else "n/a"
            console.success(
                f"Replayed dispatch {dispatch_id} (processed_at={when})",
                topic="stripe",
            )
        except Exception as exc:  # pragma: no cover - runtime
            console.error(f"Failed to replay {dispatch_id}: {exc}", topic="stripe")
    return 0


def _run_backend_dispatch(
    ctx: CLIContext,
    args: list[str],
    *,
    required_keys: Iterable[str],
) -> dict[str, Any]:
    completed = run_backend_script(
        project_root=ctx.project_root,
        script_name="stripe_dispatch.py",
        args=args,
        env_overrides={"DATABASE_ECHO": "false"},
        ctx=ctx,
    )
    if completed.returncode != 0:
        stderr = (completed.stderr or "").strip()
        stdout = (completed.stdout or "").strip()
        detail = stderr or stdout or "unknown error"
        raise CLIError(f"Stripe dispatch task failed: {detail}")

    return extract_json_payload(completed.stdout or "", required_keys=required_keys)


def _build_list_args(config: DispatchListConfig) -> list[str]:
    args = [
        "list",
        "--handler",
        config.handler,
        "--limit",
        str(config.limit),
        "--page",
        str(config.page),
    ]
    status = config.status
    if status:
        args.extend(["--status", status])
    return args


def _build_replay_args(config: DispatchReplayConfig, *, preview: bool) -> list[str]:
    args = ["replay", "--handler", config.handler, "--limit", str(config.limit)]
    if preview:
        args.append("--preview")
    if config.dispatch_ids:
        for dispatch_id in config.dispatch_ids:
            args.extend(["--dispatch-id", dispatch_id])
    if config.event_ids:
        for event_id in config.event_ids:
            args.extend(["--event-id", event_id])
    if config.status:
        args.extend(["--status", config.status])
    return args


def _preview_replay_targets(ctx: CLIContext, config: DispatchReplayConfig) -> list[str]:
    payload = _run_backend_dispatch(
        ctx,
        _build_replay_args(config, preview=True),
        required_keys=["targets"],
    )
    targets = payload.get("targets", [])
    return [str(target) for target in targets]


def _format_dispatch_row(item: dict[str, Any]) -> str:
    return (
        f"{item.get('id')}\t{item.get('status')}\thandler={item.get('handler')}\t"
        f"attempts={item.get('attempts')}\tevent={item.get('stripe_event_id')} "
        f"({item.get('event_type')})\ttenant={item.get('tenant_hint')}"
    )


def _confirm_replay(console: ConsolePort, targets: list[str], prompt: Any | None = None) -> bool:
    preview = "\n".join(str(t) for t in targets[:5])
    if len(targets) > 5:
        preview += f"\n...and {len(targets) - 5} more"
    console.info("About to replay the following dispatch IDs:", topic="stripe")
    console.print(preview)
    if prompt is not None:
        return prompt.prompt_bool(
            key="stripe_dispatch_replay",
            prompt="Proceed?",
            default=False,
        )
    answer = input("Proceed? [y/N]: ").strip().lower()
    return answer in {"y", "yes"}


__all__ = [
    "DispatchListConfig",
    "DispatchReplayConfig",
    "run_dispatch_list",
    "run_dispatch_replay",
    "run_dispatch_validate_fixtures",
    "replay_dispatches_with_repo",
]
