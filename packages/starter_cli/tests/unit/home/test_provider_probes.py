from __future__ import annotations

from starter_cli.core.status_models import ProbeResult, ProbeState
from starter_cli.workflows.home.probes.billing import billing_probe
from starter_cli.workflows.home.probes.registry import PROBE_SPECS, ProbeContext, ProbeSpec
from starter_cli.workflows.home.probes.secrets import secrets_probe


def _ctx(env: dict[str, str], *, warn_only: bool = True) -> ProbeContext:
    return ProbeContext(
        env=env,
        settings=None,
        profile="local",
        strict=not warn_only,
        warn_only=warn_only,
    )


def test_probe_registry_order_and_names():
    expected = [
        "environment",
        "ports",
        "stack",
        "database_config",
        "database",
        "redis",
        "api",
        "frontend",
        "migrations",
        "secrets",
        "billing",
        "storage",
    ]
    assert [spec.name for spec in PROBE_SPECS] == expected


def test_secrets_probe_skips_when_unset():
    result = secrets_probe(_ctx({}))
    assert result.state is ProbeState.SKIPPED
    assert "provider" in result.metadata


def test_secrets_probe_vault_uses_vault_probe(monkeypatch):
    from starter_cli.workflows.home.probes import secrets as secrets_mod

    def fake_vault_probe(*, warn_only: bool) -> ProbeResult:
        return ProbeResult(name="vault", state=ProbeState.OK, detail="ok")

    monkeypatch.setattr(secrets_mod, "vault_probe", fake_vault_probe)
    env = {
        "SECRETS_PROVIDER": "vault_dev",
        "VAULT_ADDR": "http://localhost:18200",
        "VAULT_TOKEN": "root",
    }
    result = secrets_probe(_ctx(env))
    assert result.state is ProbeState.OK
    assert result.name == "secrets"
    assert result.metadata.get("provider") == "vault_dev"


def test_secrets_probe_infisical_missing_env_warns():
    env = {"SECRETS_PROVIDER": "infisical_cloud"}
    result = secrets_probe(_ctx(env, warn_only=True))
    assert result.state is ProbeState.WARN
    assert "missing env" in (result.detail or "")


def test_secrets_probe_infisical_ok():
    env = {
        "SECRETS_PROVIDER": "infisical_cloud",
        "INFISICAL_PROJECT_ID": "proj",
        "INFISICAL_ENVIRONMENT": "dev",
        "INFISICAL_SERVICE_TOKEN": "token",
    }
    result = secrets_probe(_ctx(env))
    assert result.state is ProbeState.OK
    assert "infisical" in (result.detail or "")


def test_secrets_probe_aws_sm_ok_with_profile():
    env = {
        "SECRETS_PROVIDER": "aws_sm",
        "AWS_PROFILE": "dev",
        "AWS_REGION": "us-east-1",
    }
    result = secrets_probe(_ctx(env))
    assert result.state is ProbeState.OK
    assert "aws" in (result.detail or "")


def test_secrets_probe_azure_missing_creds_warns():
    env = {
        "SECRETS_PROVIDER": "azure_kv",
        "AZURE_KEY_VAULT_URL": "https://example.vault.azure.net",
    }
    result = secrets_probe(_ctx(env, warn_only=True))
    assert result.state is ProbeState.WARN
    assert "missing env" in (result.detail or "")


def test_billing_probe_skips_when_disabled():
    result = billing_probe(_ctx({}))
    assert result.state is ProbeState.SKIPPED
    assert "billing" == result.name


def test_billing_probe_warns_without_key_when_enabled():
    env = {"ENABLE_BILLING": "true"}
    result = billing_probe(_ctx(env, warn_only=True))
    assert result.state is ProbeState.WARN
    assert "missing" in (result.detail or "")


def test_billing_probe_errors_without_key_when_strict():
    env = {"ENABLE_BILLING": "true"}
    result = billing_probe(_ctx(env, warn_only=False))
    assert result.state is ProbeState.ERROR


def test_billing_probe_delegates_to_stripe(monkeypatch):
    from starter_cli.workflows.home.probes import billing as billing_mod

    def fake_stripe_probe(*, warn_only: bool) -> ProbeResult:
        return ProbeResult(
            name="stripe",
            state=ProbeState.OK,
            detail="ok",
            metadata={"status": 200},
        )

    monkeypatch.setattr(billing_mod, "stripe_probe", fake_stripe_probe)
    env = {"ENABLE_BILLING": "true", "STRIPE_SECRET_KEY": "sk_test_x"}
    result = billing_probe(_ctx(env))
    assert result.state is ProbeState.OK
    assert result.metadata.get("provider") == "stripe"


def test_doctor_attaches_category(monkeypatch):
    from starter_cli.core.context import build_context
    from starter_cli.workflows.home import doctor as doctor_mod

    def fake_probe(ctx):
        return ProbeResult(name="alpha", state=ProbeState.OK, detail="ok")

    monkeypatch.setattr(
        doctor_mod,
        "PROBE_SPECS",
        (ProbeSpec(name="alpha", factory=lambda ctx: fake_probe(ctx), category="secrets"),),
    )
    runner = doctor_mod.DoctorRunner(build_context(), profile="local", strict=False)
    probes = runner._run_probes()
    assert probes[0].metadata.get("category") == "secrets"
