from __future__ import annotations

from pathlib import Path

from starter_cli.services.infra import ops_models


def test_resolve_active_log_dir_prefers_current(tmp_path: Path) -> None:
    log_root = tmp_path / "var" / "log"
    current = log_root / "current"
    dated = log_root / "2025-01-01"
    current.mkdir(parents=True)
    dated.mkdir(parents=True)

    active = ops_models.resolve_active_log_dir(log_root)

    assert active == current.resolve()


def test_resolve_active_log_dir_latest_date(tmp_path: Path) -> None:
    log_root = tmp_path / "var" / "log"
    older = log_root / "2025-01-01"
    newer = log_root / "2025-02-01"
    older.mkdir(parents=True)
    newer.mkdir(parents=True)

    active = ops_models.resolve_active_log_dir(log_root)

    assert active == newer.resolve()


def test_collect_log_entries(tmp_path: Path) -> None:
    log_dir = tmp_path / "var" / "log" / "current"
    api_dir = log_dir / "api"
    api_dir.mkdir(parents=True)
    (api_dir / "all.log").write_text("hello", encoding="utf-8")

    entries = ops_models.collect_log_entries(log_dir)
    lookup = {entry.name: entry for entry in entries}

    assert lookup["api/all.log"].exists is True
    assert lookup["api/error.log"].exists is False


def test_mask_value() -> None:
    assert ops_models.mask_value(None) == "(missing)"
    assert ops_models.mask_value("abcd") == "****"
    assert ops_models.mask_value("abcdefghijk") == "abcd...hijk"

