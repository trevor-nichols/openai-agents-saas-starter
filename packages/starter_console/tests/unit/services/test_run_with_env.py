from __future__ import annotations

from pathlib import Path

import pytest

from starter_console.core import CLIError
from starter_console.services.infra.run_with_env import prepare_run_with_env


def test_prepare_run_with_env_requires_command(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\n")
    with pytest.raises(CLIError):
        prepare_run_with_env([str(env_file)], [])


def test_prepare_run_with_env_splits_tokens(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\n")
    plan = prepare_run_with_env([str(env_file), "echo", "hello"], [])
    assert plan.command == ["echo", "hello"]
    assert plan.overrides["FOO"] == "bar"


def test_prepare_run_with_env_merges_inline_overrides(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\n")
    plan = prepare_run_with_env([str(env_file), "INLINE=value"], ["echo", "hi"])
    assert plan.command == ["echo", "hi"]
    assert plan.overrides["FOO"] == "bar"
    assert plan.overrides["INLINE"] == "value"


def test_prepare_run_with_env_wraps_dash_command(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\n")
    plan = prepare_run_with_env([str(env_file)], ["-lc", "echo hi"])
    assert plan.command[:2] == ["/bin/bash", "-lc"]
