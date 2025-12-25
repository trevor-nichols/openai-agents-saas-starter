from __future__ import annotations

import pytest
from textual.app import App, ComposeResult

from starter_cli.core import CLIContext
from starter_cli.ui.panes.api_export import ApiExportPane
from starter_cli.ui.panes.auth_tokens import AuthTokensPane
from starter_cli.ui.panes.config_inventory import ConfigInventoryPane
from starter_cli.ui.panes.doctor import DoctorPane
from starter_cli.ui.panes.jwks import JwksPane
from starter_cli.ui.panes.key_rotation import KeyRotationPane
from starter_cli.ui.panes.release_db import ReleaseDbPane
from starter_cli.ui.panes.secrets import SecretsOnboardPane
from starter_cli.ui.panes.start_stop import StartStopPane
from starter_cli.ui.panes.status_ops import StatusOpsPane
from starter_cli.ui.panes.util_run_with_env import UtilRunWithEnvPane


class PaneHost(App[None]):
    def __init__(self, pane) -> None:
        super().__init__()
        self._pane = pane

    def compose(self) -> ComposeResult:
        yield self._pane


PANE_FACTORIES = [
    ("api-export", lambda ctx: ApiExportPane(ctx)),
    ("auth-tokens", lambda ctx: AuthTokensPane(ctx)),
    ("config-inventory", lambda ctx: ConfigInventoryPane(ctx)),
    ("doctor", lambda ctx: DoctorPane(ctx)),
    ("jwks", lambda ctx: JwksPane(ctx)),
    ("key-rotation", lambda ctx: KeyRotationPane(ctx)),
    ("release-db", lambda ctx: ReleaseDbPane(ctx)),
    ("secrets", lambda ctx: SecretsOnboardPane(ctx)),
    ("start-stop", lambda ctx: StartStopPane(ctx)),
    ("status-ops", lambda ctx: StatusOpsPane(ctx)),
    ("util-run-with-env", lambda ctx: UtilRunWithEnvPane(ctx)),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("pane_id,factory", PANE_FACTORIES)
async def test_new_panes_mount(tmp_path, monkeypatch, pane_id, factory) -> None:
    monkeypatch.setenv("AUTH_CLI_OUTPUT", "json")
    ctx = CLIContext(project_root=tmp_path)
    pane = factory(ctx)
    app = PaneHost(pane)

    async with app.run_test() as pilot:
        await pilot.pause()
        assert pane.id == pane_id
        assert app.query_one(type(pane)) is pane
