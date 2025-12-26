from __future__ import annotations

import os
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values

from starter_console.core import CLIError


@dataclass(frozen=True, slots=True)
class RunWithEnvPlan:
    env_files: list[str]
    command: list[str]
    overrides: dict[str, str]
    merged_env: dict[str, str]


def prepare_run_with_env(
    env_files: Sequence[str],
    exec_command: Sequence[str],
) -> RunWithEnvPlan:
    raw_env = list(env_files)
    command = list(exec_command)

    if not command:
        env_tokens, command = split_env_and_command(raw_env)
    else:
        env_tokens = raw_env

    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise CLIError("Command is required after env files (use -- to separate).")
    if command[0].startswith("-"):
        command = ["/bin/bash", *command]

    overrides = merge_env_tokens(env_tokens)
    merged_env = os.environ.copy()
    merged_env.update(overrides)

    return RunWithEnvPlan(
        env_files=env_tokens,
        command=command,
        overrides=overrides,
        merged_env=merged_env,
    )


def merge_env_tokens(files: Iterable[str]) -> dict[str, str]:
    merged: dict[str, str] = {}
    for token in files:
        if "=" in token and not token.startswith("-"):
            key, _, value = token.partition("=")
            if key:
                merged[key] = value
            continue
        merged.update(load_env_file(token))
    return merged


def split_env_and_command(tokens: list[str]) -> tuple[list[str], list[str]]:
    """Split env file tokens from command tokens.

    Rules:
    - If a literal '--' is present, everything after it is command.
    - Env files are tokens that look like .env files or KEY=VAL pairs.
    - Absolute paths that are executables (e.g., /bin/bash) are treated as commands.
    """
    if "--" in tokens:
        dash = tokens.index("--")
        return tokens[:dash], tokens[dash + 1 :]

    env_files: list[str] = []
    command: list[str] = []
    for idx, token in enumerate(tokens):
        if is_env_token(token):
            env_files.append(token)
            continue
        command = tokens[idx:]
        break
    return env_files, command


def is_env_token(token: str) -> bool:
    path = Path(token)
    inline_kv = "=" in token and not token.startswith("-")
    if inline_kv:
        return True
    name = path.name
    return (
        name.startswith(".env")
        or name.endswith(".env")
        or name.endswith(".env.local")
        or path.suffix in {".env", ".compose"}
    )


def load_env_file(path: str) -> dict[str, str]:
    file_path = Path(path)
    if not file_path.is_file():
        return {}
    values = dotenv_values(file_path)
    return {key: value for key, value in values.items() if value is not None}


__all__ = [
    "RunWithEnvPlan",
    "is_env_token",
    "load_env_file",
    "merge_env_tokens",
    "prepare_run_with_env",
    "split_env_and_command",
]
