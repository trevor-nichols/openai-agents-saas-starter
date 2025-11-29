from __future__ import annotations

import json
from pathlib import Path

import pytest
from starter_cli.core import CLIError
from starter_cli.workflows.setup import (
    HeadlessInputProvider,
    InteractiveInputProvider,
    load_answers_files,
    merge_answer_overrides,
)


def test_load_answers_files_merges(tmp_path: Path) -> None:
    file_a = tmp_path / "a.json"
    file_b = tmp_path / "b.json"
    file_a.write_text(json.dumps({"ENVIRONMENT": "production", "DEBUG": False}), encoding="utf-8")
    file_b.write_text(json.dumps({"PORT": 9000}), encoding="utf-8")

    answers = load_answers_files([file_a, file_b])

    assert answers == {
        "ENVIRONMENT": "production",
        "DEBUG": "False",
        "PORT": "9000",
    }


def test_merge_answer_overrides_handles_duplicates() -> None:
    base = {"PORT": "8000"}
    overrides = ["PORT=9001", "secret_key=abc"]

    merged = merge_answer_overrides(base, overrides)

    assert merged["PORT"] == "9001"
    assert merged["SECRET_KEY"] == "abc"


def test_headless_provider_missing_value_raises() -> None:
    provider = HeadlessInputProvider(answers={})
    with pytest.raises(CLIError):
        provider.prompt_string(
            key="PORT",
            prompt="Port",
            default=None,
            required=True,
        )


def test_interactive_prefill_short_circuits(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = InteractiveInputProvider(prefill={"PORT": "8100"})

    def fail_prompt(_: str) -> str:
        raise AssertionError("prompt should not be called when prefill exists")

    monkeypatch.setattr("builtins.input", fail_prompt)
    value = provider.prompt_string(
        key="PORT",
        prompt="Port",
        default="8000",
        required=True,
    )

    assert value == "8100"
