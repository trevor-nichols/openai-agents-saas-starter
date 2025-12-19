# Status & Notifications Domain

Platform-facing status surface that:
- Publishes the current platform snapshot for the marketing status page and RSS.
- Manages subscriber lifecycle (email + webhook) for incident alerts.
- Fans incidents out to subscribers and optional Slack channels.

## Components
- `status_service.py` — thin façade over a `PlatformStatusRepository`. The default is `InMemoryStatusRepository` (`app/infrastructure/status/repository.py`) that returns static demo data; swap in a real repository when observability feeds exist.
- `status_subscription_service.py` — creates/verifies/revokes subscriptions with rate limiting, hashing/peppering of tokens, webhook HMAC challenges, and unsubscribe tokens. Persists through `StatusSubscriptionRepository` (Postgres implementation lives in `infrastructure/persistence/status/postgres.py`).
- `status_alert_dispatcher.py` — pulls active subscriptions, filters by severity, and delivers incidents via email, webhook (HMAC `X-Status-Signature`), and optional Slack. It also regenerates unsubscribe tokens on demand.

## HTTP surface (`/api/v1/status`)
- `GET /status` — public platform snapshot (`PlatformStatusSnapshot` → `PlatformStatusResponse`).
- `GET /status/rss` — RSS feed of incidents (same snapshot rendered as RSS).
- `POST /status/subscriptions` — create email/webhook subscription. Webhooks require an authenticated token with `status:manage`; email flows are public but rate limited.
- `POST /status/subscriptions/verify` — confirm email token and activate.
- `POST /status/subscriptions/challenge` — confirm webhook challenge token and activate.
- `GET /status/subscriptions` — list subscriptions (requires `status:manage`, supports tenant scoping + cursor pagination).
- `DELETE /status/subscriptions/{id}` — revoke via unsubscribe token (email) or authenticated `status:manage`.
- `POST /status/incidents/{incident_id}/resend` — replay a known incident to matching subscribers (and Slack) with an optional tenant filter (`status:manage` required).

## Runtime wiring
- `main.lifespan` builds the services only when a status subscription repository is available (`get_status_subscription_repository`). If no `DATABASE_URL` or encryption secret is present, subscription/dispatch endpoints return `503`, but the public snapshot and RSS still work via the in-memory repository.
- Persistence uses the `status_subscriptions` table (managed by Alembic). Run `just migrate` after configuring the database to create it.
- Secrets: subscription targets, webhook secrets, and unsubscribe tokens are encrypted at rest using `STATUS_SUBSCRIPTION_ENCRYPTION_KEY` (or `SECRET_KEY` as a fallback).
- Links in emails/webhooks are generated with `APP_PUBLIC_URL` and include unsubscribe parameters.

## Configuration knobs developers care about
- Email delivery: `RESEND_EMAIL_ENABLED`, `RESEND_API_KEY`, `RESEND_DEFAULT_FROM`, `RESEND_BASE_URL` (optional). If disabled, emails are logged/queued but not sent.
- Token + rate limiting: `STATUS_SUBSCRIPTION_TOKEN_TTL_MINUTES`, `STATUS_SUBSCRIPTION_EMAIL_RATE_LIMIT_PER_HOUR`, `STATUS_SUBSCRIPTION_IP_RATE_LIMIT_PER_HOUR`, `STATUS_SUBSCRIPTION_TOKEN_PEPPER`, `STATUS_SUBSCRIPTION_WEBHOOK_TIMEOUT_SECONDS`.
- Encryption: `STATUS_SUBSCRIPTION_ENCRYPTION_KEY` (preferred) or `SECRET_KEY`.
- Slack fan-out: `ENABLE_SLACK_STATUS_NOTIFICATIONS`, `SLACK_STATUS_BOT_TOKEN`, `SLACK_STATUS_DEFAULT_CHANNELS`, `SLACK_STATUS_TENANT_CHANNEL_MAP`, `SLACK_STATUS_RATE_LIMIT_WINDOW_SECONDS`, `SLACK_STATUS_MAX_RETRIES`.
- Rate limiter backend: configure `RATE_LIMIT_REDIS_URL` (or `REDIS_URL`) so subscription creation limits are enforced; if absent, limits are effectively disabled.

## Local expectations
- Out of the box (no DB/Resend/Slack), only `GET /api/v1/status` and `GET /api/v1/status/rss` are available using static demo data; subscription endpoints return `503` until the repository is configured.
- To exercise the full flow locally: set `DATABASE_URL`, run `just migrate`, set `STATUS_SUBSCRIPTION_ENCRYPTION_KEY` (or `SECRET_KEY`), point `APP_PUBLIC_URL` to your frontend, configure Redis for rate limiting, and enable Resend/Slack as needed. Then create a subscription, confirm via email or webhook challenge, and use the resend endpoint to fan out a test incident.
