from __future__ import annotations

from starter_cli.adapters.io.console import console
from starter_cli.commands.infra import collect_dependency_statuses


def run_preflight(context) -> None:
    """Collect dependency health and store it on the wizard context."""

    console.info("Running preflight dependency checks …", topic="preflight")
    statuses = list(collect_dependency_statuses())
    context.dependency_statuses = statuses

    missing = []
    for status in statuses:
        if status.status == "ok":
            version = f" — {status.version}" if status.version else ""
            location = status.command_display or "(detected)"
            console.success(f"{status.name}: {location}{version}", topic="preflight")
        else:
            missing.append(status)
            console.warn(f"{status.name}: missing. {status.hint}", topic="preflight")

    if missing:
        required = ", ".join(dep.name for dep in missing)
        console.warn(
            f"Missing dependencies detected: {required}. "
            "Resolve before enabling one-stop automation.",
            topic="preflight",
        )
    else:
        console.success("All prerequisite tooling detected.", topic="preflight")


__all__ = ["run_preflight"]
