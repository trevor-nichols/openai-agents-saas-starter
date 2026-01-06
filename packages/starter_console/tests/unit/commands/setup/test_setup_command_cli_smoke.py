from __future__ import annotations

import os
from pathlib import Path
from collections.abc import Sequence
from typing import cast

from starter_console import app as console_app
from starter_console.container import ApplicationContainer
from starter_console.core import CLIContext
from starter_console.ports.console import ConsolePort


class _SmokeContainer(ApplicationContainer):
    def __init__(self, project_root: Path) -> None:
        super().__init__()
        self._project_root = project_root

    def create_context(
        self,
        *,
        env_files: Sequence[Path] | None = None,
        skip_env: bool = False,
        quiet_env: bool = False,
    ) -> CLIContext:
        return CLIContext(
            project_root=self._project_root,
            env_files=tuple(env_files) if env_files is not None else (),
            console=cast(ConsolePort, self.console),
            skip_env=skip_env,
            quiet_env=quiet_env,
        )


def test_setup_wizard_cli_non_interactive_end_to_end(tmp_path: Path) -> None:
    snapshot = dict(os.environ)
    try:
        (tmp_path / "apps" / "api-service").mkdir(parents=True, exist_ok=True)
        (tmp_path / "apps" / "api-service" / ".env.local").write_text(
            "",
            encoding="utf-8",
        )
        container = _SmokeContainer(tmp_path)
        args = [
            "--skip-env",
            "setup",
            "wizard",
            "--profile",
            "demo",
            "--non-interactive",
            "--var",
            "OPENAI_API_KEY=test-key",
            "--var",
            "BILLING_RETRY_DEPLOYMENT_MODE=inline",
            "--no-auto-infra",
            "--no-auto-secrets",
            "--no-auto-stripe",
            "--no-auto-sso",
            "--no-auto-migrations",
            "--no-auto-redis",
            "--no-auto-geoip",
            "--no-auto-dev-user",
            "--no-auto-demo-token",
        ]
        exit_code = console_app.main(args, container=container)
        assert exit_code == 0

        manifest_path = tmp_path / "var/reports/profile-manifest.json"
        assert manifest_path.exists()
    finally:
        os.environ.clear()
        os.environ.update(snapshot)
