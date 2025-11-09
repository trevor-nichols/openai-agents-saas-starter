"""Helper to merge env files before running a command."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Iterable

from dotenv import dotenv_values


def load_env(path: str) -> dict[str, str]:
    file = Path(path)
    if not file.is_file():
        return {}
    values = dotenv_values(file)
    return {key: value for key, value in values.items() if value is not None}


def merge_env(files: Iterable[str]) -> dict[str, str]:
    merged: dict[str, str] = {}
    for env_file in files:
        merged.update(load_env(env_file))
    return merged


def main(argv: list[str]) -> int:
    if "--" not in argv:
        print(
            "Usage: run_with_env.py <env_file>... -- <command> [args...]",
            file=sys.stderr,
        )
        return 1

    sep_index = argv.index("--")
    env_files = argv[:sep_index]
    command = argv[sep_index + 1 :]

    if not command:
        print("Command is required after --", file=sys.stderr)
        return 1

    env = os.environ.copy()
    env.update(merge_env(env_files))

    os.execvpe(command[0], command, env)
    return 0  # never reached


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
