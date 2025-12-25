from __future__ import annotations

import io
import json

from starter_console import app as cli_app
from starter_console.adapters.io.console import console as cli_console


def test_config_dump_schema_json(monkeypatch) -> None:
    buffer = io.StringIO()
    monkeypatch.setattr(cli_console, "stream", buffer)
    exit_code = cli_app.main(
        [
            "--skip-env",
            "config",
            "dump-schema",
            "--format",
            "json",
        ]
    )
    assert exit_code == 0
    data = json.loads(buffer.getvalue())
    assert any(entry["env_var"] == "ENVIRONMENT" for entry in data)
    env_entry = next(entry for entry in data if entry["env_var"] == "ENVIRONMENT")
    assert env_entry["wizard_prompted"] is True
    assert env_entry["required"] is False


def test_config_dump_schema_table(monkeypatch) -> None:
    buffer = io.StringIO()
    monkeypatch.setattr(cli_console, "stream", buffer)
    exit_code = cli_app.main(["--skip-env", "config", "dump-schema"])
    assert exit_code == 0
    output = buffer.getvalue()
    assert "Env Var" in output
    assert "DATABASE_URL" in output


def test_config_write_inventory(monkeypatch, tmp_path) -> None:
    buffer = io.StringIO()
    monkeypatch.setattr(cli_console, "stream", buffer)
    destination = tmp_path / "inventory.md"
    exit_code = cli_app.main(
        [
            "--skip-env",
            "config",
            "write-inventory",
            "--path",
            str(destination),
        ]
    )
    assert exit_code == 0
    body = destination.read_text(encoding="utf-8")
    assert "Starter Console Environment Inventory" in body
    assert "| Env Var |" in body
