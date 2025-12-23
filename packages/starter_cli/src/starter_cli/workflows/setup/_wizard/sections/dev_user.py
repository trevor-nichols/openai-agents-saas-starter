from __future__ import annotations

import secrets

from starter_cli.adapters.io.console import console

from ...demo_token import DemoTokenConfig
from ...dev_user import DevUserConfig
from ...inputs import InputProvider
from ..context import WizardContext


def run(context: WizardContext, provider: InputProvider) -> None:
    console.section(
        "Dev User",
        "Capture the demo dev user you want seeded after setup. Leave the password blank to "
        "auto-generate a strong one; it will be shown once and never written to disk.",
    )

    if context.profile != "demo":
        console.info("Dev user seeding only runs for demo profile; skipping.", topic="dev-user")
        context.dev_user_config = None
        return

    email = provider.prompt_string(
        key="DEV_USER_EMAIL",
        prompt="Dev user email",
        default=context.current("DEV_USER_EMAIL") or "dev@example.com",
        required=True,
    )
    display = provider.prompt_string(
        key="DEV_USER_DISPLAY_NAME",
        prompt="Display name (optional)",
        default=context.current("DEV_USER_DISPLAY_NAME") or "Dev Admin",
        required=False,
    )
    tenant_slug = provider.prompt_string(
        key="DEV_USER_TENANT_SLUG",
        prompt="Tenant slug",
        default=context.current("TENANT_DEFAULT_SLUG") or "default",
        required=True,
    )
    tenant_name = provider.prompt_string(
        key="DEV_USER_TENANT_NAME",
        prompt="Tenant name",
        default=context.current("DEV_USER_TENANT_NAME") or "Default Tenant",
        required=True,
    )
    role = provider.prompt_string(
        key="DEV_USER_ROLE",
        prompt="Tenant role",
        default=context.current("DEV_USER_ROLE") or "admin",
        required=True,
    )
    password = provider.prompt_secret(
        key="DEV_USER_PASSWORD",
        prompt="Password (blank to auto-generate)",
        existing=None,
        required=False,
    )
    locked = provider.prompt_bool(
        key="DEV_USER_LOCKED",
        prompt="Lock the account after creation?",
        default=False,
    )

    generated = False
    if not password:
        password = secrets.token_urlsafe(20)
        generated = True
        console.info("Generated a strong password for the dev user.", topic="dev-user")

    context.dev_user_config = DevUserConfig(
        email=email.strip(),
        display_name=(display or "").strip(),
        tenant_slug=tenant_slug.strip(),
        tenant_name=tenant_name.strip(),
        role=role.strip(),
        password=password,
        locked=locked,
        generated_password=generated,
        rotate_existing=True,
    )
    context.demo_token_config = DemoTokenConfig(
        account="demo-bot",
        scopes=["chat:write", "conversations:read"],
        tenant_slug=tenant_slug.strip() or None,
        fingerprint="wizard-demo",
        force=False,
    )
    _scrub_recorded_answer(provider, "DEV_USER_PASSWORD")
    if context.state_store:
        context.state_store.data.get("answers", {}).pop("DEV_USER_PASSWORD", None)


def _scrub_recorded_answer(provider: InputProvider, key: str) -> None:
    """Remove sensitive answers from any attached recorders (export/state)."""
    visited: set[int] = set()
    current: object | None = provider
    while current and id(current) not in visited:
        visited.add(id(current))
        recorder = getattr(current, "recorder", None)
        if recorder and hasattr(recorder, "_answers"):
            recorder._answers.pop(key, None)
        next_provider = getattr(current, "provider", None) or getattr(current, "_provider", None)
        current = next_provider


__all__ = ["run"]
