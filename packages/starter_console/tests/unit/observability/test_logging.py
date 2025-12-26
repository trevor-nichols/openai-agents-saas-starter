from __future__ import annotations

from datetime import date
from pathlib import Path

from starter_contracts.observability.logging import LoggingRuntimeConfig
from starter_console.observability import logging as console_logging


def test_textual_log_path_uses_console_component_root(tmp_path: Path) -> None:
    runtime = LoggingRuntimeConfig(
        service="starter-console",
        environment="test",
        log_level="INFO",
        logging_sinks="file",
        log_root=str(tmp_path),
        logging_file_path="var/log/starter-console.log",
        logging_file_max_mb=1,
        logging_file_backups=1,
        logging_max_days=0,
        logging_duplex_error_file=False,
        component="starter-console",
        handler_namespace="starter_contracts.observability.logging.sinks",
        default_file_path="var/log/starter-console.log",
        repo_root=tmp_path,
    )

    expected_root = tmp_path / date.today().isoformat() / "starter-console"
    log_path = console_logging._resolve_textual_log_path(runtime)

    assert log_path == expected_root / "textual.log"
    assert log_path.parent.exists()
