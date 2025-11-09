# Resend Transactional Email Runbook

Last updated: November 9, 2025

This runbook explains how to operate the Resend-backed email delivery path for verification and password reset flows in anything-agents.

## Prerequisites

1. Verify a sending domain inside Resend and provision a production API key.
2. Ensure Redis and Postgres are running; token stores remain in Redis and user data in Postgres.
3. Keep the following environment variables configured:
   - `RESEND_EMAIL_ENABLED=true`
   - `RESEND_API_KEY=re_...`
   - `RESEND_DEFAULT_FROM="Your Name <support@example.com>"`
   - `APP_PUBLIC_URL=https://app.example.com`
   - Optional template IDs: `RESEND_EMAIL_VERIFICATION_TEMPLATE_ID`, `RESEND_PASSWORD_RESET_TEMPLATE_ID`

## Enabling Resend

1. Populate the env vars above in `.env.local` (dev) or deployment secrets.
2. Deploy. The service builders automatically switch to the Resend notifier when `RESEND_EMAIL_ENABLED=true`.
3. Watch metrics/alerts (see Monitoring below) for the first few sends.

## Template Strategy

- Hosted templates are optional. Leave the template ID env vars empty to use the built-in HTML/text layouts defined in `app/presentation/emails/templates.py`.
- Hosted template requirements (if used): must accept `token`, `app_name`, and `expires_at` variables. Subject/from/reply-to in the payload override template defaults.
- Links derive from `APP_PUBLIC_URL`:
  - Verification: `<APP_PUBLIC_URL>/verify-email?token=...`
  - Password reset: `<APP_PUBLIC_URL>/reset-password?token=...`

### Previewing Local Templates

Use pytest snapshots or run this helper snippet in a shell:

```bash
python - <<'PY'
from datetime import UTC, datetime
from app.core.config import Settings
from app.presentation.emails import render_verification_email
settings = Settings(app_public_url="https://app.dev")
content = render_verification_email(settings, token="demo123", expires_at=datetime.now(UTC))
print(content.html)
print("---")
print(content.text)
PY
```

## Monitoring

Metrics (Prometheus):
- `email_delivery_attempts_total{category="email_verification|password_reset",result="success|error|timeout"}`
- `email_delivery_latency_seconds` (same labels).

Logs:
- `auth.email_verification_notification` and `auth.password_reset_notification` show per-send outcomes.
- `notifications.resend_send` captures Resend-level diagnostics (message ID, failure reason).

Alerting guidance:
- Trigger on sustained `result="error"` or `result="timeout"` rates >5/min for five minutes.

## Troubleshooting

1. **Email route returns 502**
   - Causes: Resend outage, invalid API key, network timeout.
   - Steps: check logs for `notifications.resend_send` entries, ensure API key is valid, retry.
2. **Users report missing emails**
   - Inspect Prometheus metrics for spikes.
   - Verify domain reputation in Resend dashboard (bounces, complaints).
   - Use Resend “Emails” tab to confirm send/bounce state via message ID logged in `notifications.resend_send`.
3. **Local development**
   - Keep `RESEND_EMAIL_ENABLED=false` to use the logging notifier; emails are not sent externally.

## Operational Checklist

- [ ] Environment secrets set (`RESEND_API_KEY`, `RESEND_DEFAULT_FROM`, `APP_PUBLIC_URL`).
- [ ] Sending domain verified in Resend.
- [ ] Monitoring dashboard includes `email_delivery_*` metrics.
- [ ] Runbook updated when template variables or delivery logic change.
