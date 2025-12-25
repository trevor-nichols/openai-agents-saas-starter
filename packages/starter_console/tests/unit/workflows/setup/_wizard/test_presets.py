from __future__ import annotations

from pathlib import Path

from starter_console.adapters.env import EnvFile
from starter_console.core import CLIContext
from starter_console.workflows.setup._wizard.context import WizardContext
from starter_console.workflows.setup._wizard.presets import apply_hosting_preset
from starter_contracts.secrets.models import SecretsProviderLiteral
from starter_contracts.storage.models import StorageProviderLiteral


def _build_context(tmp_path: Path) -> WizardContext:
    backend_env_path = tmp_path / "apps" / "api-service" / ".env.local"
    backend_env_path.parent.mkdir(parents=True, exist_ok=True)
    backend_env_path.write_text("", encoding="utf-8")
    frontend_env_path = tmp_path / "apps" / "web-app" / ".env.local"
    frontend_env_path.parent.mkdir(parents=True, exist_ok=True)
    frontend_env_path.write_text("", encoding="utf-8")
    ctx = CLIContext(project_root=tmp_path, env_files=(backend_env_path,))
    return WizardContext(
        cli_ctx=ctx,
        profile="demo",
        backend_env=EnvFile(backend_env_path),
        frontend_env=EnvFile(frontend_env_path),
        frontend_path=frontend_env_path,
    )


def test_local_docker_preset_defaults(tmp_path: Path) -> None:
    context = _build_context(tmp_path)
    context.hosting_preset = "local_docker"

    apply_hosting_preset(context)

    assert context.current("STARTER_LOCAL_DATABASE_MODE") == "compose"
    assert context.current("REDIS_URL") == "redis://localhost:6379/0"
    assert context.current("SECRETS_PROVIDER") == SecretsProviderLiteral.VAULT_DEV.value
    assert context.current("STORAGE_PROVIDER") == StorageProviderLiteral.MINIO.value
    assert context.current("ENABLE_BILLING") == "false"


def test_cloud_managed_preset_defaults(tmp_path: Path) -> None:
    context = _build_context(tmp_path)
    context.hosting_preset = "cloud_managed"
    context.cloud_provider = "azure"

    apply_hosting_preset(context)

    assert context.current("STARTER_LOCAL_DATABASE_MODE") == "external"
    assert context.current("SECRETS_PROVIDER") == SecretsProviderLiteral.AZURE_KV.value
    assert context.current("STORAGE_PROVIDER") == StorageProviderLiteral.AZURE_BLOB.value
    assert context.current("ENABLE_BILLING") == "true"
