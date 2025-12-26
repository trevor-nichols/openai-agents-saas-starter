from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
from typing import Any, cast

import pytest


def _ensure_azure_stubs() -> None:
    try:
        spec = importlib.util.find_spec("azure.keyvault.secrets")
    except ModuleNotFoundError:  # pragma: no cover - namespace pkg missing
        spec = None
    if spec is not None:  # pragma: no cover - real dependency installed
        return

    azure_pkg = cast(Any, sys.modules.setdefault("azure", types.ModuleType("azure")))

    core_pkg = cast(Any, types.ModuleType("azure.core"))
    exceptions_mod = cast(Any, types.ModuleType("azure.core.exceptions"))

    class AzureError(Exception):
        pass

    exceptions_mod.AzureError = AzureError
    core_pkg.exceptions = exceptions_mod
    sys.modules["azure.core"] = core_pkg
    sys.modules["azure.core.exceptions"] = exceptions_mod
    azure_pkg.core = core_pkg

    identity_mod = cast(Any, types.ModuleType("azure.identity"))

    class _StubCredential:
        def __init__(self, *args, **kwargs) -> None:  # pragma: no cover - trivial
            pass

    identity_mod.ChainedTokenCredential = _StubCredential
    identity_mod.ClientSecretCredential = _StubCredential
    identity_mod.DefaultAzureCredential = _StubCredential
    identity_mod.ManagedIdentityCredential = _StubCredential
    sys.modules["azure.identity"] = identity_mod
    azure_pkg.identity = identity_mod

    keyvault_pkg = cast(Any, types.ModuleType("azure.keyvault"))
    secrets_mod = cast(Any, types.ModuleType("azure.keyvault.secrets"))

    class SecretClient:  # pragma: no cover - stub implementation
        def __init__(self, *_, **__) -> None:
            pass

        def get_secret(self, *_args, **_kwargs) -> None:
            raise RuntimeError("SecretClient stub should be patched in tests")

    secrets_mod.SecretClient = SecretClient
    keyvault_pkg.secrets = secrets_mod
    sys.modules["azure.keyvault"] = keyvault_pkg
    sys.modules["azure.keyvault.secrets"] = secrets_mod
    azure_pkg.keyvault = keyvault_pkg


_ensure_azure_stubs()

from starter_console.core import CLIContext  # noqa: E402


@pytest.fixture()
def cli_ctx(tmp_path: Path) -> CLIContext:
    return CLIContext(project_root=tmp_path, env_files=())
