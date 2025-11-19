"""Architecture tests enforcing service import boundaries."""

from __future__ import annotations

import ast
from pathlib import Path


def _find_repo_root() -> Path:
    current = Path(__file__).resolve()
    for candidate in current.parents:
        if (candidate / "pyproject.toml").exists():
            return candidate
    raise RuntimeError("Unable to locate repository root (pyproject.toml not found)")


REPO_ROOT = _find_repo_root()
APP_ROOT = REPO_ROOT / "api-service" / "app"
CLI_ROOT = REPO_ROOT / "starter_cli"
SCRIPTS_ROOT = REPO_ROOT / "scripts"
SCAN_ROOTS = [APP_ROOT, CLI_ROOT, SCRIPTS_ROOT]

BANNED_IMPORTS: dict[str, str] = {
    "app.services.billing_service": "Use app.services.billing.billing_service instead.",
    "app.services.billing_events": "Use app.services.billing.billing_events instead.",
    "app.services.payment_gateway": "Use app.services.billing.payment_gateway instead.",
    "app.services.stripe_dispatcher": "Use app.services.billing.stripe.dispatcher instead.",
    "app.services.stripe_event_models": "Use app.services.billing.stripe.event_models instead.",
    "app.services.stripe_retry_worker": "Use app.services.billing.stripe.retry_worker instead.",
    "app.services.email_verification_service": (
        "Use app.services.signup.email_verification_service instead."
    ),
    "app.services.invite_service": "Use app.services.signup.invite_service instead.",
    "app.services.password_recovery_service": (
        "Use app.services.signup.password_recovery_service instead."
    ),
    "app.services.signup_request_service": (
        "Use app.services.signup.signup_request_service instead."
    ),
    "app.services.signup_service": "Use app.services.signup.signup_service instead.",
    "app.services.status_service": "Use app.services.status.status_service instead.",
    "app.services.status_alert_dispatcher": (
        "Use app.services.status.status_alert_dispatcher instead."
    ),
    "app.services.status_subscription_service": (
        "Use app.services.status.status_subscription_service instead."
    ),
    "app.services.tenant_settings_service": (
        "Use app.services.tenant.tenant_settings_service instead."
    ),
    "app.services.user_service": "Use app.services.users.user_service instead.",
    "app.services.rate_limit_service": (
        "Use app.services.shared.rate_limit_service instead."
    ),
}


def _iter_python_files() -> list[Path]:
    files: list[Path] = []
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            files.append(path)
    return files


def _collect_violations() -> list[str]:
    violations: list[str] = []
    for path in _iter_python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name
                    if module_name in BANNED_IMPORTS:
                        msg = BANNED_IMPORTS[module_name]
                        violations.append(
                            f"{path}:{node.lineno} imports {module_name}. {msg}"
                        )
            elif isinstance(node, ast.ImportFrom):
                module_name = node.module or ""
                # Allow relative imports to be handled by Ruff; here only check absolute names.
                if module_name in BANNED_IMPORTS:
                    msg = BANNED_IMPORTS[module_name]
                    violations.append(f"{path}:{node.lineno} imports {module_name}. {msg}")
    return violations


def test_service_import_boundaries() -> None:
    violations = _collect_violations()
    assert not violations, "\n".join(violations)
