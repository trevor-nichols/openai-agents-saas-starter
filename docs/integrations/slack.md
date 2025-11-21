# Slack Status Notifications

Slack is the first officially supported integration surface for the Starter stack. The
`StatusAlertDispatcher` now broadcasts every incident (manual or automated) to the channels defined
in your environment files, so operators can mirror the email/webhook fan-out inside their incident
rooms without custom code.

## Prerequisites

1. Create a Slack app in the workspace that should receive incidents.
2. Grant the following scopes (minimum): `chat:write`, `chat:write.public` (if posting into public
   channels that don’t already include the bot), and `channels:read` / `groups:read` if you plan to
   look up channel IDs automatically.
3. Install the app to the workspace and capture the **Bot User OAuth Token** (starts with
   `xoxb-`).
4. Collect the channel IDs (recommended) or channel names for each incident room. Slack’s channel
   picker (`Ctrl/Cmd+K`) → “View channel details” → “Channel ID” is the fastest manual path.

## Environment Variables

| Variable | Description |
| --- | --- |
| `ENABLE_SLACK_STATUS_NOTIFICATIONS` | Master switch. When `true`, every incident invokes the Slack adapter. |
| `SLACK_STATUS_BOT_TOKEN` | Bot OAuth token with `chat:write` scope. Stored encrypted via `.env.local`; never logged. |
| `SLACK_STATUS_DEFAULT_CHANNELS` | Comma-separated or JSON array of channel IDs/names that always receive incidents. |
| `SLACK_STATUS_TENANT_CHANNEL_MAP` | JSON object mapping tenant IDs to arrays of channel IDs. Overrides the defaults when provided. |
| `SLACK_API_BASE_URL` | Override for Slack’s API endpoint (defaults to `https://slack.com/api`). Useful for local testing or EU isolation once Slack exposes it. |
| `SLACK_HTTP_TIMEOUT_SECONDS` | Per-request timeout. Defaults to `5.0`. |
| `SLACK_STATUS_RATE_LIMIT_WINDOW_SECONDS` | Per-channel throttle window (default `1.0s`). Keeps us under Slack’s “≈1 message/second per channel” rule. |
| `SLACK_STATUS_MAX_RETRIES` | Maximum delivery attempts after 5xx, `ratelimited`, or transport failures (default `3`). |

## Wizard Flow

Run `python -m starter_cli.app setup wizard` (interactive or headless) and answer the new prompts in
the **Integrations** milestone:

1. “Enable Slack notifications for status incidents?” – toggles `ENABLE_SLACK_STATUS_NOTIFICATIONS`.
2. “Slack bot token (chat:write scope)” – stored as `SLACK_STATUS_BOT_TOKEN`.
3. “Default Slack channel IDs …” – accepts comma-separated values or JSON arrays. Use channel IDs
   (e.g., `C0123456`) for maximum stability.
4. “Tenant override map …” – optional JSON (e.g., `{ "tenant-id": ["C0123", "C0456"] }`).
5. “Send a Slack test message now?” – when `true`, the wizard calls `chat.postMessage` against the
   first default channel and records a verification artifact in `var/reports/verification-artifacts.json`.

Headless runs can supply the same fields via answers files:

```json
{
  "ENABLE_SLACK_STATUS_NOTIFICATIONS": "true",
  "SLACK_STATUS_BOT_TOKEN": "xoxb-***",
  "SLACK_STATUS_DEFAULT_CHANNELS": "[\"C012345\", \"C067890\"]",
  "SLACK_STATUS_TENANT_CHANNEL_MAP": "{\"tenant-id\":[\"C999999\"]}"
}
```

## Runtime Behaviour

- The dispatcher sends one message per configured channel **after** finishing email/webhook fan-out.
- Per-channel throttling ensures we never exceed Slack’s special-tier guideline of ≈1 message per
  second. If Slack still returns `HTTP 429`, we honor `Retry-After` before retrying.
- Failures raise `SlackNotificationError`, log a structured event, and update the Prometheus metrics
  `slack_notification_attempts_total` / `slack_notification_latency_seconds` so you can alert on
  integration health.
- JSON payloads mirror the email/webhook content (service, state, impact, timestamp) and render via
  Slack’s `mrkdwn` blocks.

## Operational Tips

- Keep the bot in every target channel (private channels require an explicit `/invite`).
- Rotate the bot token like other secrets: re-run the wizard or `starter_cli config set` to update
  the env file, then redeploy.
- Slack announced on **29 May 2025** that APIs such as `conversations.history` now default to Tier 1
  rate limits (1 request/minute) for new non-Marketplace apps. Our notifier only posts messages, but
  if you extend it to read threads remember those tighter quotas apply beginning **3 March 2026** for
  legacy apps as well.

For additional integrations (PagerDuty, CRM, etc.) follow the same pattern: add a service under
`app/services/integrations/`, wire it into the dispatcher, expose env knobs via the wizard, and log
verification artifacts so operators have evidence for audits.

