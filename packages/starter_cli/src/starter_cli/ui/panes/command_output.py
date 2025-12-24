from __future__ import annotations

from starter_cli.services.ops_commands import CommandResult


def format_command_result(label: str, result: CommandResult) -> str:
    if result.error:
        return result.error
    returncode = result.returncode if result.returncode is not None else "unknown"
    if result.stdout:
        return f"{label} exited with {returncode}\n{result.stdout}"
    return f"{label} exited with {returncode}"


__all__ = ["format_command_result"]
