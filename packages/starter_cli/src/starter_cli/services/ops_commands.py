from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class CommandResult:
    returncode: int | None
    stdout: str
    error: str | None


async def run_command(*, command: list[str], cwd: Path) -> CommandResult:
    try:
        proc = await asyncio.create_subprocess_exec(
            *command,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, _ = await proc.communicate()
        text = stdout.decode(errors="ignore").strip() if stdout else ""
        return CommandResult(returncode=proc.returncode, stdout=text, error=None)
    except FileNotFoundError as exc:
        return CommandResult(returncode=None, stdout="", error=f"Command not found: {exc}")
    except Exception as exc:  # pragma: no cover - defensive
        return CommandResult(returncode=None, stdout="", error=f"Command failed: {exc}")


__all__ = ["CommandResult", "run_command"]
