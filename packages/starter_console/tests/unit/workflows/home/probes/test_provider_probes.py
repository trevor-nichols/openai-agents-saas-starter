from __future__ import annotations

from starter_console.core.status_models import ProbeResult, ProbeState
from starter_console.workflows.home.probes.registry import PROBE_SPECS, ProbeContext, ProbeSpec


def _ctx(env: dict[str, str], *, warn_only: bool = True) -> ProbeContext:
    return ProbeContext(
        env=env,
        settings=None,
        profile="demo",
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
        "sso",
        "storage",
    ]
    assert [spec.name for spec in PROBE_SPECS] == expected


def test_secrets_probe_skips_when_unset():
    from starter_console.workflows.home.probes import secrets as secrets_mod

    result = secrets_mod.secrets_probe(_ctx({}))
    assert result.state == ProbeState.SKIPPED
    assert "provider" in result.metadata


def test_secrets_probe_vault_uses_vault_probe(monkeypatch):
    from starter_console.workflows.home.probes import secrets as secrets_mod

    def fake_vault_probe(*, warn_only: bool) -> ProbeResult:
        return ProbeResult(name="vault", state=ProbeState.OK, detail="ok")

    monkeypatch.setattr(secrets_mod, "vault_probe", fake_vault_probe)
    env = {
        "SECRETS_PROVIDER": "vault_dev",
        "VAULT_ADDR": "http://localhost:18200",
        "VAULT_TOKEN": "root",
    }
    result = secrets_mod.secrets_probe(_ctx(env))
    assert result.state == ProbeState.OK
    assert result.name == "secrets"
    assert result.metadata.get("provider") == "vault_dev"


def test_secrets_probe_infisical_missing_env_warns():
    from starter_console.workflows.home.probes import secrets as secrets_mod

    env = {"SECRETS_PROVIDER": "infisical_cloud"}
    result = secrets_mod.secrets_probe(_ctx(env, warn_only=True))
    assert result.state == ProbeState.WARN
    assert "missing env" in (result.detail or "")


def test_secrets_probe_infisical_ok():
    from starter_console.workflows.home.probes import secrets as secrets_mod

    env = {
        "SECRETS_PROVIDER": "infisical_cloud",
        "INFISICAL_PROJECT_ID": "proj",
        "INFISICAL_ENVIRONMENT": "dev",
        "INFISICAL_SERVICE_TOKEN": "token",
    }
    result = secrets_mod.secrets_probe(_ctx(env))
    assert result.state == ProbeState.OK
    assert "infisical" in (result.detail or "")


def test_secrets_probe_aws_sm_ok_with_profile():
    from starter_console.workflows.home.probes import secrets as secrets_mod

    env = {
        "SECRETS_PROVIDER": "aws_sm",
        "AWS_PROFILE": "dev",
        "AWS_REGION": "us-east-1",
    }
    result = secrets_mod.secrets_probe(_ctx(env))
    assert result.state == ProbeState.OK
    assert "aws" in (result.detail or "")


def test_secrets_probe_azure_missing_creds_warns():
    from starter_console.workflows.home.probes import secrets as secrets_mod

    env = {
        "SECRETS_PROVIDER": "azure_kv",
        "AZURE_KEY_VAULT_URL": "https://example.vault.azure.net",
    }
    result = secrets_mod.secrets_probe(_ctx(env, warn_only=True))
    assert result.state == ProbeState.WARN
    assert "missing env" in (result.detail or "")


def test_billing_probe_skips_when_disabled():
    from starter_console.workflows.home.probes import billing as billing_mod

    result = billing_mod.billing_probe(_ctx({}))
    assert result.state == ProbeState.SKIPPED
    assert "billing" == result.name


def test_billing_probe_warns_without_key_when_enabled():
    from starter_console.workflows.home.probes import billing as billing_mod

    env = {"ENABLE_BILLING": "true"}
    result = billing_mod.billing_probe(_ctx(env, warn_only=True))
    assert result.state == ProbeState.WARN
    assert "missing" in (result.detail or "")


def test_billing_probe_errors_without_key_when_strict():
    from starter_console.workflows.home.probes import billing as billing_mod

    env = {"ENABLE_BILLING": "true"}
    result = billing_mod.billing_probe(_ctx(env, warn_only=False))
    assert result.state == ProbeState.ERROR


def test_billing_probe_delegates_to_stripe(monkeypatch):
    from starter_console.workflows.home.probes import billing as billing_mod

    def fake_stripe_probe(*, warn_only: bool) -> ProbeResult:
        return ProbeResult(
            name="stripe",
            state=ProbeState.OK,
            detail="ok",
            metadata={"status": 200},
        )

    monkeypatch.setattr(billing_mod, "stripe_probe", fake_stripe_probe)
    env = {"ENABLE_BILLING": "true", "STRIPE_SECRET_KEY": "sk_test_x"}
    result = billing_mod.billing_probe(_ctx(env))
    assert result.state == ProbeState.OK
    assert result.metadata.get("provider") == "stripe"


def test_sso_probe_skips_when_disabled():
    from starter_console.workflows.home.probes import sso as sso_mod

    result = sso_mod.sso_probe(_ctx({}))
    assert result.state == ProbeState.SKIPPED
    assert result.metadata.get("provider") == "google"


def test_sso_probe_warns_on_missing_tenant_scope():
    from starter_console.workflows.home.probes import sso as sso_mod

    env = {
        "SSO_GOOGLE_ENABLED": "true",
        "SSO_GOOGLE_SCOPE": "tenant",
    }
    result = sso_mod.sso_probe(_ctx(env, warn_only=True))
    assert result.state == ProbeState.WARN
    assert "tenant scope" in (result.detail or "")


def test_sso_probe_warns_on_global_scope_with_tenant_values():
    from starter_console.workflows.home.probes import sso as sso_mod

    env = {
        "SSO_GOOGLE_ENABLED": "true",
        "SSO_GOOGLE_SCOPE": "global",
        "SSO_GOOGLE_TENANT_ID": "tenant-id",
    }
    result = sso_mod.sso_probe(_ctx(env, warn_only=True))
    assert result.state == ProbeState.WARN
    assert "global scope" in (result.detail or "")


def test_sso_probe_ok_with_backend_config(monkeypatch):
    import json
    import subprocess

    from starter_console.workflows.home.probes import sso as sso_mod

    payload = {
        "result": "ok",
        "provider_key": "google",
        "config_source": "global",
        "enabled": True,
        "auto_provision_policy": "invite_only",
        "default_role": "member",
        "pkce_required": True,
        "allowed_domains_count": 0,
    }

    def fake_run_backend_script(*_args, **_kwargs):
        return subprocess.CompletedProcess(
            args=["hatch"],
            returncode=0,
            stdout=json.dumps(payload),
            stderr="",
        )

    monkeypatch.setattr(sso_mod, "run_backend_script", fake_run_backend_script)

    env = {
        "SSO_GOOGLE_ENABLED": "true",
        "AUTH_CACHE_REDIS_URL": "redis://localhost:6379/0",
        "SECRET_KEY": "secret",
    }
    result = sso_mod.sso_probe(_ctx(env))
    assert result.state == ProbeState.OK
    assert "configured" in (result.detail or "")


def test_sso_probe_warns_when_not_configured(monkeypatch):
    import json
    import subprocess

    from starter_console.workflows.home.probes import sso as sso_mod

    payload = {
        "result": "not_configured",
        "provider_key": "google",
        "config_source": None,
    }

    def fake_run_backend_script(*_args, **_kwargs):
        return subprocess.CompletedProcess(
            args=["hatch"],
            returncode=0,
            stdout=json.dumps(payload),
            stderr="",
        )

    monkeypatch.setattr(sso_mod, "run_backend_script", fake_run_backend_script)

    env = {
        "SSO_GOOGLE_ENABLED": "true",
        "AUTH_CACHE_REDIS_URL": "redis://localhost:6379/0",
        "SECRET_KEY": "secret",
    }
    result = sso_mod.sso_probe(_ctx(env, warn_only=True))
    assert result.state == ProbeState.WARN
    assert "not configured" in (result.detail or "")


def test_doctor_attaches_category(monkeypatch):
    from starter_console.core.context import build_context
    from starter_console.workflows.home import doctor as doctor_mod

    def fake_probe(ctx):
        return ProbeResult(name="alpha", state=ProbeState.OK, detail="ok")

    monkeypatch.setattr(
        doctor_mod,
        "PROBE_SPECS",
        (ProbeSpec(name="alpha", factory=lambda ctx: fake_probe(ctx), category="secrets"),),
    )
    runner = doctor_mod.DoctorRunner(build_context(), profile="demo", strict=False)
    probes = runner._run_probes()
    assert probes[0].metadata.get("category") == "secrets"
