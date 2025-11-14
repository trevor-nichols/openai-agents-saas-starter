# Status Alert Subscription Contract

**Last Updated:** 2025-11-12  
**Owner:** Platform Foundations (Status Workstream)  
**Status:** Proposed – awaiting backend plumbing sign-off

## 1. Goals & Non-Goals

### Goals
- Give operators and enterprise tenants a first-class way to subscribe to status updates via email or webhook.
- Keep the contract simple enough for public marketing surfaces while enforcing strong validation and scope-based access for privileged channels.
- Ensure every subscription can be audited, verified, and revoked without data loss.
- Reuse existing infrastructure (Postgres, Redis, Stripe event bus) so we do not introduce bespoke queues.

### Non-Goals
- Building a full incident-management UI (Linear remains the system of record).
- Real-time push via WebSockets/SSE (RSS and the status API already address that use case).
- Shipping SMS/push notification channels in this iteration.

## 2. User Stories

| Story | Description |
|-------|-------------|
| **STS-001** | Prospective customer subscribes with an email address from `/status` without logging in. Double opt-in ensures compliance. |
| **STS-002** | Tenant admin adds a webhook endpoint (PagerDuty/VictorOps) scoped to their tenant. Requires authentication and `status:manage` scope. |
| **STS-003** | Platform operator lists and revokes stale subscriptions directly from the CLI. |
| **STS-004** | Status worker fan-outs incident notifications to all matching subscriptions (channel + severity). |

## 3. Data Model

| Field | Type | Notes |
|-------|------|-------|
| `subscription_id` | UUID (ULID acceptable) | Primary key returned to the client. |
| `channel` | Enum `email | webhook` | Drives validation + delivery pipeline. |
| `target` | String | Email address or HTTPS URL. Stored encrypted at rest. |
| `severity_filter` | Enum `all | major | maintenance` | Defaults to `major`. |
| `tenant_id` | UUID? | Nullable. Present when created from an authenticated tenant context. |
| `created_by` | String | `public` or user ID for auditing. |
| `status` | Enum `pending_verification | active | revoked` | Email channel starts as `pending_verification`; webhook can be `active` immediately once verified via signed challenge. |
| `verification_token` | String | Short-lived token emailed to confirms email channel subscriptions. |
| `created_at / updated_at` | Timestamps | For auditing + cleanup. |

## 4. API Surface

> Prefix: `/api/v1/status/subscriptions`

### 4.1 Create Subscription — `POST /`

**Auth:**
- Email channel: optional (public).  
- Webhook channel: requires authenticated session (JWT) + `status:manage` scope (tenant admins + platform operators).

**Request Body**

```json
{
  "channel": "email",
  "target": "sre@example.com",
  "severity_filter": "major"
}
```

| Field | Type | Required | Rules |
|-------|------|----------|-------|
| `channel` | string | ✅ | `email` or `webhook`. |
| `target` | string | ✅ | Email validated via RFC 5322 helpers; webhook requires HTTPS URL + 5s timeout budget. |
| `severity_filter` | string | ❌ | Defaults to `major`; supports `all`, `major`, `maintenance`. |
| `metadata` | object | ❌ | Free-form `{ label: string, notes?: string }` stored with tenant-facing descriptions. |

**Responses**

| Code | Body |
|------|------|
| `201` | `{ "subscription_id": "sub_123", "status": "pending_verification", "webhook_secret": "..." }` (secret only present for webhook channels) |
| `202` | Webhook channel accepted but awaiting signed challenge response. |
| `400` | Invalid payload/target. |
| `401/403` | Missing auth or scope on webhook channel. |
| `409` | Duplicate active subscription for the same channel + target + severity. |

---

### 4.2 Verify Email Token — `POST /{subscription_id}/verify`

Used by the link in the double opt-in email.

**Request Body**

```json
{ "token": "v3rify-123" }
```

**Response**

`200 OK` → `{ "subscription_id": "sub_123", "status": "active" }`  
`400/404` → invalid or expired token.

---

### 4.3 Send Webhook Challenge — `POST /{subscription_id}/challenge`

Triggered automatically after creation for webhook channels. Server posts a signed payload to the provided `target`. Clients must echo the `challenge` value back via this endpoint within 10 minutes.

**Challenge Payload (server → client)**

```json
{
  "challenge": "string",
  "subscription_id": "sub_123",
  "timestamp": "2025-11-12T18:02:00Z"
}
```

Clients must respond with:

```json
{ "challenge": "string" }
```

Success moves the subscription to `active`.

---

### 4.4 List Subscriptions — `GET /`

**Auth:** Tenant admins see their tenant’s subscriptions automatically; platform operators (role `platform_admin`) can pass `tenant_id` query param for audits or public (tenant-less) subscriptions.

**Query Params**: `channel`, `status`, `tenant_id`, pagination (`cursor`, `limit`).

**Response**

```json
{
  "items": [
    {
      "subscription_id": "sub_123",
      "channel": "email",
      "target_masked": "s***@example.com",
      "severity_filter": "major",
      "status": "active",
      "created_at": "2025-11-12T18:00:00Z"
    }
  ],
  "next_cursor": null
}
```

`target_masked` keeps PII out of browser logs.

---

### 4.5 Delete Subscription — `DELETE /{subscription_id}`

Soft delete (status → `revoked`). Requires email-token auth (link in unsubscribe footer) **or** authenticated tenant/operator session.

- Authenticated operators/tenants: `DELETE /{id}` with bearer token → `204 No Content`.
- Public unsubscribe: `DELETE /{id}?token=<unsubscribe_token>` (linked in every email footer) → `204 No Content`.

---

### 4.6 CLI Helpers

- `starter-cli status subscriptions list` – wraps `GET /api/v1/status/subscriptions`.
- `starter-cli status subscriptions revoke <id>` – wraps `DELETE /{id}`.
- CLI always authenticates via service account and uses platform scopes.
- `starter-cli status incidents resend <incident_id> [--severity major|maintenance|all] [--tenant <uuid>]` – replays an incident via the dispatcher.

## 5. Delivery Pipeline

1. **Event Source:** Incident lifecycle (`incident_created`, `incident_updated`, `incident_resolved`) plus uptime degradations emitted by the status poller.
2. **Fan-out Worker:** New async task (`StatusAlertDispatcher`) pulls pending events, resolves matching subscriptions (`severity_filter`, tenant scope), and hands off to channel-specific adapters.
3. **Channels:**
   - Email → existing transactional email provider (Resend) with templated subject/body.
   - Webhook → Signed JSON payload with HMAC SHA-256 using per-subscription secret (`webhook_secret` column). Replays tracked via nonce cache (Redis TTL 10 minutes).
4. **Observability:**
   - Prometheus counters `status_alerts_sent_total{channel,status}`.
   - Structured logs on enqueue/send/failure referencing `subscription_id` & `incident_id`.
5. **Rate Limiting:** Per-subscription cooldown (e.g., 1 notification per minute) to avoid flooding.

## 6. Frontend Integration

### Status Page CTA
- Replace the placeholder buttons in `app/(marketing)/status/page.tsx` with a `SubscribeStatusCTA` component once the POST endpoint lands.
- Component responsibilities:
  - Mode toggle (email vs webhook) with channel-specific fields.
  - Uses `useStatusSubscriptionMutation` hook (TanStack Query) that wraps `POST /api/v1/status/subscriptions`.
  - Surfaces success toast + inline copy showing next steps (verify email, respond to webhook challenge).
  - Falls back to linking the RSS feed while the mutation is pending/failed to maintain UX continuity.

### Account Settings (Future)
- Authenticated tenants can manage subscriptions under `/account/service-accounts` or a new `/account/status` tab using the `GET/DELETE` endpoints.

## 7. Security & Compliance Notes
- **Email Verification**: tokens expire after 24h; subsequent attempts rotate the token and resend email.
- **Webhook Signing**: each subscription stores `webhook_secret` (32 bytes). Every delivery includes headers `X-Status-Signature` and `X-Status-Timestamp`. Clients verify HMAC and freshness.
- **PII Handling**: `target` encrypted at rest via existing Vault transit helper; only masked version ever leaves the server.
- **Rate Limiting**: `POST /` is limited to 5 attempts/hour per IP for public users, 30/hour for authenticated tenants.
- **RBAC**: `status:manage` scope already exists for platform operators; extend tenant admin role to include it when the feature flag is enabled.

## 8. Open Questions & Decisions
1. **Webhook template customization** – Keep the payload standardized for GA. Custom templates introduce extra signing/validation paths and complicate incident triage. Revisit only if enterprise tenants request it at scale.
2. **Manual resend controls** – Provide a minimal CLI command (`starter-cli status incidents resend --incident <id> [--tenant <id>]`) for platform operators. This re-enqueues the last published incident through the dispatcher, giving ops an audited escape hatch without UI work.
3. **reCAPTCHA / bot mitigation** – Launch without reCAPTCHA. IP rate limits + double opt-in already curb abuse. Keep a feature flag in the POST handler so we can bolt on Cloudflare Turnstile or reCAPTCHA v3 later if marketing sees spam.

## 9. Next Steps
- ✅ Document contract (this file).  
- ✅ Record decisions for webhook templates, resend controls, and captcha.  
- ✅ Align on storage + create `status_subscriptions` table (2025-11-12).  
- ✅ Scaffold FastAPI endpoints, Pydantic models, and service layer (2025-11-12).  
- ✅ Implement Postgres repository + rate-limit enforcement (2025-11-12).  
- ✅ Add `StatusAlertDispatcher` worker + CLI resend/list commands (2025-11-12).  
- ⏳ Update `/status` CTA + TanStack mutation once backend scaffolding lands.
