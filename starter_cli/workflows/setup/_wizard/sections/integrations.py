"""Integration prompts for the setup wizard."""

from __future__ import annotations

import json

import httpx

from starter_cli.adapters.io.console import console

from ...inputs import InputProvider
from ..context import WizardContext


def run(context: WizardContext, provider: InputProvider) -> None:
    console.section(
        "Integrations",
        "Connect operator tooling such as Slack for proactive notifications.",
    )
    _configure_slack_status(context, provider)


def _configure_slack_status(context: WizardContext, provider: InputProvider) -> None:
    default_enabled = context.current_bool("ENABLE_SLACK_STATUS_NOTIFICATIONS", False)
    enabled = provider.prompt_bool(
        key="ENABLE_SLACK_STATUS_NOTIFICATIONS",
        prompt="Enable Slack notifications for status incidents?",
        default=default_enabled,
    )
    context.set_backend_bool("ENABLE_SLACK_STATUS_NOTIFICATIONS", enabled)
    if not enabled:
        console.info("Slack status notifications disabled.", topic="wizard")
        return

    token = provider.prompt_secret(
        key="SLACK_STATUS_BOT_TOKEN",
        prompt="Slack bot token (chat:write scope)",
        existing=context.current("SLACK_STATUS_BOT_TOKEN"),
        required=True,
    )
    context.set_backend("SLACK_STATUS_BOT_TOKEN", token, mask=True)

    existing_channels = context.current("SLACK_STATUS_DEFAULT_CHANNELS") or ""
    default_channels = existing_channels or "#incidents"
    channels = provider.prompt_string(
        key="SLACK_STATUS_DEFAULT_CHANNELS",
        prompt="Default Slack channel IDs (comma-separated or JSON list)",
        default=default_channels,
        required=True,
    )
    context.set_backend("SLACK_STATUS_DEFAULT_CHANNELS", channels, mask=False)

    tenant_map_default = context.current("SLACK_STATUS_TENANT_CHANNEL_MAP") or ""
    tenant_map = provider.prompt_string(
        key="SLACK_STATUS_TENANT_CHANNEL_MAP",
        prompt="Tenant override map (JSON {tenant_id:[channel,…]})",
        default=tenant_map_default,
        required=False,
    )
    if tenant_map:
        context.set_backend("SLACK_STATUS_TENANT_CHANNEL_MAP", tenant_map, mask=False)
    else:
        context.unset_backend("SLACK_STATUS_TENANT_CHANNEL_MAP")

    send_test = provider.prompt_bool(
        key="SLACK_STATUS_SEND_TEST",
        prompt="Send a Slack test message now?",
        default=False,
    )
    if send_test:
        _send_test_message(context, token=token, channels_input=channels)


def _send_test_message(context: WizardContext, *, token: str, channels_input: str) -> None:
    channels = _parse_channels_input(channels_input)
    if not channels:
        console.warn("No Slack channels provided; skipping test message.", topic="wizard")
        return
    base_url = context.current("SLACK_API_BASE_URL") or "https://slack.com/api"
    timeout = float(context.current("SLACK_HTTP_TIMEOUT_SECONDS") or 5.0)
    payload = {
        "channel": channels[0],
        "text": "✅ Slack integration verified via Starter CLI.",
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8",
    }
    try:
        with httpx.Client(base_url=base_url.rstrip("/"), timeout=timeout) as client:
            response = client.post("/chat.postMessage", headers=headers, json=payload)
        data = response.json()
    except Exception as exc:  # pragma: no cover - network failures
        console.error(f"Slack test failed: {exc}", topic="wizard")
        context.record_verification(
            provider="slack",
            identifier=channels[0],
            status="failed",
            detail=str(exc),
        )
        return
    if response.status_code == 200 and data.get("ok"):
        console.success("Slack test message delivered.", topic="wizard")
        context.record_verification(
            provider="slack",
            identifier=channels[0],
            status="passed",
            detail="chat.postMessage",
        )
        return
    detail = str(data.get("error") or response.text)
    console.warn(f"Slack test returned {detail}.", topic="wizard")
    context.record_verification(
        provider="slack",
        identifier=channels[0],
        status="failed",
        detail=detail,
    )


def _parse_channels_input(raw: str) -> list[str]:
    trimmed = (raw or "").strip()
    if not trimmed:
        return []
    try:
        parsed = json.loads(trimmed)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, list):
        return [str(item).strip() for item in parsed if str(item).strip()]
    return [segment.strip() for segment in trimmed.split(",") if segment.strip()]


__all__ = ["run"]
