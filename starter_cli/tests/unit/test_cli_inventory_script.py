from __future__ import annotations

from scripts.cli import verify_env_inventory


def test_verify_env_inventory_script_passes() -> None:
    assert verify_env_inventory.run() == 0


def test_verify_env_inventory_accepts_six_column_table(monkeypatch, tmp_path) -> None:
    doc = tmp_path / "inventory.md"
    doc.write_text(
        """
| Env Var | Type | Default | Wizard | Required | Description |
| --- | --- | --- | --- | --- | --- |
| `EXAMPLE` | `str` | foo | ✅ | ✅ | Sample |
        """.strip(),
        encoding="utf-8",
    )

    entry = verify_env_inventory.EnvEntry(env_var="EXAMPLE", wizard_prompted=True)
    monkeypatch.setattr(verify_env_inventory, "DOC_PATH", doc)
    monkeypatch.setattr(
        verify_env_inventory,
        "_collect_settings_entries",
        lambda: {"EXAMPLE": entry},
    )

    assert verify_env_inventory.run() == 0
