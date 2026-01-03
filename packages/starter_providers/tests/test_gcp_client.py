from __future__ import annotations

import pytest
from google.auth import exceptions as auth_exceptions

from starter_providers.secrets.gcp_client import (
    GCPSecretManagerClient,
    GCPSecretManagerError,
    secretmanager,
)


class _StubSecretManagerClient:
    def access_secret_version(self, request):  # noqa: ANN001 - signature mirrors SDK
        raise auth_exceptions.GoogleAuthError("missing credentials")


def test_gcp_client_wraps_init_auth_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise_auth_error():  # noqa: ANN001 - mimics SDK constructor signature
        raise auth_exceptions.DefaultCredentialsError("missing credentials")

    monkeypatch.setattr(
        secretmanager,
        "SecretManagerServiceClient",
        _raise_auth_error,
    )

    with pytest.raises(GCPSecretManagerError) as excinfo:
        GCPSecretManagerClient(project_id="demo-project")

    assert "Failed to initialize GCP Secret Manager client" in str(excinfo.value)


def test_gcp_client_wraps_auth_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        secretmanager,
        "SecretManagerServiceClient",
        lambda: _StubSecretManagerClient(),
    )
    client = GCPSecretManagerClient(project_id="demo-project")

    with pytest.raises(GCPSecretManagerError) as excinfo:
        client.get_secret_value_optional("auth-signing-secret")

    assert "Failed to read secret" in str(excinfo.value)
