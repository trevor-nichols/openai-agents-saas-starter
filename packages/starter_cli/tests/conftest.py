"""Pytest configuration for starter_cli tests."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from typing import Any, cast
from starter_contracts import config as shared_config

# Make sure repo-local packages and shared test helpers are importable before
# importing anything that relies on them (e.g., api-service test utilities).
_REPO_ROOT = Path(__file__).resolve().parents[3]
_API_DIR = _REPO_ROOT / "apps" / "api-service"
_API_SRC = _API_DIR / "src"
_API_TESTS = _API_DIR / "tests"
for _path in (_REPO_ROOT, _API_DIR, _API_SRC, _API_TESTS):
    _path_str = str(_path)
    if _path_str not in sys.path:
        sys.path.insert(0, _path_str)

def _install_google_stubs() -> None:
    """Stub google cloud modules so FastAPI imports don't require heavy deps."""

    import types

    if "google" in sys.modules:
        return

    class _DummyGcsError(Exception):
        ...

    class _DummyNotFound(_DummyGcsError):
        ...

    google: Any = types.ModuleType("google")
    api_core: Any = types.ModuleType("google.api_core")
    api_core.exceptions = cast(
        Any,
        types.SimpleNamespace(
            GoogleAPIError=_DummyGcsError, NotFound=_DummyNotFound
        ),
    )

    class _DummyBlob:
        def __init__(self, key: str) -> None:
            self.key = key
            self.size = 0
            self.content_type = ""
            self.crc32c = ""
            self.client = types.SimpleNamespace(_credentials=None)

        def generate_signed_url(self, **_: object) -> str:
            return "https://example.invalid"

        def reload(self) -> None:
            return None

        def delete(self) -> None:
            return None

        def upload_from_string(self, data: bytes, **__: object) -> None:
            self.size = len(data)
            return None

    class _DummyBucket:
        def __init__(self, name: str) -> None:
            self.name = name
            self.iam_configuration = types.SimpleNamespace(
                uniform_bucket_level_access_enabled=False
            )
            self.location = "US"

        def blob(self, key: str) -> _DummyBlob:
            return _DummyBlob(key)

        def exists(self) -> bool:
            return True

        def create(self) -> None:
            return None

    class _DummyClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            self.args = args
            self.kwargs = kwargs

        def bucket(self, name: str) -> _DummyBucket:
            return _DummyBucket(name)

        def list_buckets(self, page_size: int = 1):
            return []

    storage_mod: Any = types.ModuleType("google.cloud.storage")
    storage_mod.Client = _DummyClient

    cloud: Any = types.ModuleType("google.cloud")
    cloud.storage = storage_mod

    oauth2: Any = types.ModuleType("google.oauth2")
    service_account: Any = types.ModuleType("google.oauth2.service_account")

    class _DummyCreds:
        @classmethod
        def from_service_account_info(cls, info: object) -> "_DummyCreds":
            return cls()

        @classmethod
        def from_service_account_file(cls, path: str) -> "_DummyCreds":
            return cls()

    service_account.Credentials = _DummyCreds
    oauth2.service_account = service_account

    sys.modules["google"] = google
    sys.modules["google.api_core"] = api_core
    sys.modules["google.api_core.exceptions"] = cast(Any, api_core.exceptions)
    sys.modules["google.cloud"] = cloud
    sys.modules["google.cloud.storage"] = storage_mod
    sys.modules["google.oauth2"] = oauth2
    sys.modules["google.oauth2.service_account"] = service_account


_install_google_stubs()


def _install_azure_stubs() -> None:
    """Stub Azure SDK modules so FastAPI imports don't require heavy deps."""

    import types

    if "azure" in sys.modules:
        return

    class _DummyAzureError(Exception):
        ...

    class _DummyResourceNotFound(_DummyAzureError):
        ...

    import importlib.machinery

    azure_mod: Any = types.ModuleType("azure")
    azure_mod.__path__ = []
    azure_mod.__spec__ = importlib.machinery.ModuleSpec("azure", loader=None)
    core_mod: Any = types.ModuleType("azure.core")
    core_mod.__path__ = []
    core_mod.__spec__ = importlib.machinery.ModuleSpec("azure.core", loader=None)
    core_exceptions: Any = types.ModuleType("azure.core.exceptions")
    core_exceptions.__spec__ = importlib.machinery.ModuleSpec(
        "azure.core.exceptions", loader=None
    )
    core_exceptions.AzureError = _DummyAzureError
    core_exceptions.ResourceNotFoundError = _DummyResourceNotFound
    core_mod.exceptions = core_exceptions
    core_credentials: Any = types.ModuleType("azure.core.credentials")
    core_credentials.__spec__ = importlib.machinery.ModuleSpec(
        "azure.core.credentials", loader=None
    )

    class _DummyTokenCredential:
        def __init__(self, *_: object, **__: object) -> None:
            return None

    core_credentials.TokenCredential = _DummyTokenCredential
    core_mod.credentials = core_credentials

    identity_mod: Any = types.ModuleType("azure.identity")
    identity_mod.__path__ = []
    identity_mod.__spec__ = importlib.machinery.ModuleSpec("azure.identity", loader=None)

    class _DummyDefaultAzureCredential:
        def __init__(self, *args: object, **kwargs: object) -> None:
            self.args = args
            self.kwargs = kwargs

    class _DummyChainedTokenCredential:
        def __init__(self, *_: object, **__: object) -> None:
            return None

    class _DummyClientSecretCredential:
        def __init__(self, *_: object, **__: object) -> None:
            return None

    class _DummyManagedIdentityCredential:
        def __init__(self, *_: object, **__: object) -> None:
            return None

    identity_mod.DefaultAzureCredential = _DummyDefaultAzureCredential
    identity_mod.ChainedTokenCredential = _DummyChainedTokenCredential
    identity_mod.ClientSecretCredential = _DummyClientSecretCredential
    identity_mod.ManagedIdentityCredential = _DummyManagedIdentityCredential

    storage_mod: Any = types.ModuleType("azure.storage")
    storage_mod.__path__ = []
    storage_mod.__spec__ = importlib.machinery.ModuleSpec("azure.storage", loader=None)
    blob_mod: Any = types.ModuleType("azure.storage.blob")
    blob_mod.__spec__ = importlib.machinery.ModuleSpec("azure.storage.blob", loader=None)

    class _DummyBlobSasPermissions:
        def __init__(self, **_: object) -> None:
            return None

    class _DummyContentSettings:
        def __init__(self, **_: object) -> None:
            return None

    class _DummyBlobServiceClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            self.args = args
            self.kwargs = kwargs

        @classmethod
        def from_connection_string(cls, *args: object, **kwargs: object) -> "_DummyBlobServiceClient":
            return cls(*args, **kwargs)

        def get_container_client(self, *_: object, **__: object):
            return types.SimpleNamespace(
                get_container_properties=lambda: None,
                create_container=lambda: None,
            )

        def get_blob_client(self, *_: object, **__: object):
            return types.SimpleNamespace(
                url="https://example.invalid/blob",
                get_blob_properties=lambda: types.SimpleNamespace(
                    size=0,
                    content_settings=types.SimpleNamespace(content_type=None),
                ),
                download_blob=lambda: types.SimpleNamespace(readall=lambda: b""),
                upload_blob=lambda *_args, **_kwargs: None,
                delete_blob=lambda *_args, **_kwargs: None,
            )

        def get_account_information(self) -> None:
            return None

    def _generate_blob_sas(**_: object) -> str:
        return "dummy-sas"

    blob_mod.BlobSasPermissions = _DummyBlobSasPermissions
    blob_mod.BlobServiceClient = _DummyBlobServiceClient
    blob_mod.ContentSettings = _DummyContentSettings
    blob_mod.generate_blob_sas = _generate_blob_sas
    storage_mod.blob = blob_mod

    keyvault_mod: Any = types.ModuleType("azure.keyvault")
    keyvault_mod.__path__ = []
    keyvault_mod.__spec__ = importlib.machinery.ModuleSpec("azure.keyvault", loader=None)
    keyvault_secrets_mod: Any = types.ModuleType("azure.keyvault.secrets")
    keyvault_secrets_mod.__spec__ = importlib.machinery.ModuleSpec(
        "azure.keyvault.secrets", loader=None
    )

    class _DummySecretClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            self.args = args
            self.kwargs = kwargs

        def get_secret(self, *_: object, **__: object):
            return types.SimpleNamespace(value="dummy")

        def set_secret(self, *_: object, **__: object) -> None:
            return None

    keyvault_secrets_mod.SecretClient = _DummySecretClient

    sys.modules["azure"] = azure_mod
    sys.modules["azure.core"] = core_mod
    sys.modules["azure.core.exceptions"] = core_exceptions
    sys.modules["azure.core.credentials"] = core_credentials
    sys.modules["azure.identity"] = identity_mod
    sys.modules["azure.storage"] = storage_mod
    sys.modules["azure.storage.blob"] = blob_mod
    sys.modules["azure.keyvault"] = keyvault_mod
    sys.modules["azure.keyvault.secrets"] = keyvault_secrets_mod


_install_azure_stubs()

from app.core import settings as api_config
from tests.utils.pytest_stripe import (
    configure_stripe_replay_option,
    register_stripe_replay_marker,
    skip_stripe_replay_if_disabled,
)


@pytest.fixture(autouse=True, scope="session")
def _ensure_import_paths() -> None:
    """Guarantee repo-local packages (starter_cli, api-service/src/app) are importable in CI."""

    repo_root = _REPO_ROOT
    api_dir = _API_DIR

    # Configure deterministic key storage so auth-dependent tests can sign tokens.
    test_keyset = api_dir / "tests" / "fixtures" / "keysets" / "test_keyset.json"
    os.environ["AUTH_KEY_STORAGE_BACKEND"] = "file"
    os.environ["AUTH_KEY_STORAGE_PATH"] = str(test_keyset)
    os.environ["STARTER_CLI_SKIP_VAULT_PROBE"] = "true"
    os.environ.setdefault("STARTER_CLI_SKIP_ENV", "true")
    # Ensure API app boots without external services during contract tests.
    os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    os.environ.setdefault("OPENAI_API_KEY", "test-key")
    # Avoid background workers that assume migrated schemas.
    os.environ.setdefault("ENABLE_VECTOR_STORE_SYNC_WORKER", "false")
    os.environ.setdefault("AUTO_CREATE_VECTOR_STORE_FOR_FILE_SEARCH", "false")
    # Ensure settings pick up the overrides
    api_config.get_settings.cache_clear()
    shared_config.get_settings.cache_clear()


def pytest_addoption(parser: pytest.Parser) -> None:
    configure_stripe_replay_option(parser)


def pytest_configure(config: pytest.Config) -> None:
    register_stripe_replay_marker(config)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    skip_stripe_replay_if_disabled(config, items)


@pytest.fixture(autouse=True, scope="session")
def _sqlite_jsonb_compat() -> None:
    """Downgrade JSONB columns for SQLite-backed tests to avoid DDL errors."""

    from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
    from app.infrastructure.persistence.models import base

    for table in base.Base.metadata.tables.values():
        for col in table.columns:
            if getattr(col.type, "__class__", type(None)).__name__ == "JSONB":
                col.type = SQLITE_JSON()


@pytest.fixture(autouse=True)
def _restore_env_after_test():
    """Ensure per-test environment isolation and clear settings caches."""

    snapshot = dict(os.environ)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(snapshot)
        api_config.get_settings.cache_clear()
        shared_config.get_settings.cache_clear()
