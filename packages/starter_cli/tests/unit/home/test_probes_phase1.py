from __future__ import annotations

import httpx
from starter_cli.core.status_models import ProbeState
from starter_cli.workflows.home.probes import db, migrations, redis, stripe, vault


def test_db_probe_warns_on_unsupported_scheme(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///tmp/test.db")
    result = db.db_probe()
    assert result.state is ProbeState.WARN
    assert "Unsupported" in (result.detail or "")


def test_db_probe_promotes_ping_failure(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")
    monkeypatch.setattr(db, "tcp_check", lambda *args, **kwargs: (True, "connected"))
    monkeypatch.setattr(db, "_pg_ping", lambda *args, **kwargs: (False, "boom"))

    result = db.db_probe()
    assert result.state is ProbeState.ERROR
    assert "boom" in (result.detail or "")


def test_redis_probe_ping_failure(monkeypatch):
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setattr(redis, "tcp_check", lambda *args, **kwargs: (True, "connected"))
    monkeypatch.setattr(redis, "_redis_ping", lambda *args, **kwargs: (False, "no pong"))

    result = redis.redis_probe()
    assert result.state is ProbeState.ERROR
    assert "no pong" in (result.detail or "")


def test_migrations_probe_mismatch(monkeypatch, tmp_path):
    # create fake versions dir
    versions_dir = tmp_path / "versions"
    versions_dir.mkdir()
    (versions_dir / "20250101_first.py").write_text("#")
    monkeypatch.setattr(migrations, "VERSIONS_DIR", versions_dir)
    monkeypatch.setattr(migrations, "_db_revision", lambda url: ("20240101", "ok"))
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")

    result = migrations.migrations_probe()
    assert result.state is ProbeState.WARN
    assert "code at" in (result.detail or "")


def test_stripe_probe_warns_on_http_error(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_123")

    def fake_get(*args, **kwargs):
        raise httpx.HTTPError("network down")

    monkeypatch.setattr(
        stripe, "_stripe_ping", lambda key, timeout=1.5: (False, "http_error: x", None)
    )
    result = stripe.stripe_probe(warn_only=True)
    assert result.state is ProbeState.WARN


def test_vault_probe_missing_addr_warn(monkeypatch):
    monkeypatch.delenv("VAULT_ADDR", raising=False)
    monkeypatch.delenv("VAULT_TOKEN", raising=False)
    result = vault.vault_probe(warn_only=True)
    assert result.state is ProbeState.WARN
    assert "VAULT_ADDR" in (result.detail or "")
