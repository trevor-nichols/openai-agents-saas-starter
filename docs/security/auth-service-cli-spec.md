# AuthService Service-Account Issuance CLI — Specification (Draft)

**Status:** Ready for review  
**Last Updated:** 2025-11-06  
**Owners:** Backend Auth Pod · Platform Security Guild

---

## 1. Objectives

- Provide a deterministic, auditable mechanism for non-interactive consumers (analytics jobs, billing workers, support console, synthetic monitors) to obtain tenant-scoped refresh tokens.  
- Integrate smoothly with CI/CD pipelines and on-call runbooks without exposing private keys or bypassing Vault access controls.  
- Emit structured logs/metrics for compliance and troubleshooting.

## 2. High-Level Flow

```
Operator / CI Job
   │
   ├──> `auth tokens issue-service-account --account analytics-batch --tenant <uuid> --scopes conversations:read`
   │
   ├── CLI authenticates against Vault using machine identity (AppRole / OIDC workload)
   │
   ├── CLI calls AuthService issuance endpoint (mTLS or signed JWT) with:
   │        - Service account identifier
   │        - Tenant ID (optional for global accounts)
   │        - Requested scopes (subset of approved list)
   │        - Token lifetime hints (optional; bounded by policy)
   │
   └── AuthService validates request → mints refresh token → returns:
            {
              "refresh_token": "<jwt>",
              "expires_at": "...",
              "scopes": [...],
              "tenant_id": "...",
              "kid": "...",
              "issued_at": "..."
            }
```

## 3. CLI Surface

### 3.1 Command Layout

- Binary/entrypoint: `python -m auth_cli` (packaged alongside backend code) or dedicated script `./bin/auth`.  
- Primary command: `auth tokens issue-service-account`.  
- Subcommands (future): `auth tokens revoke`, `auth keys rotate`, etc.

### 3.2 Parameters

| Flag | Required | Description |
| --- | --- | --- |
| `--account` / `-a` | Yes | Logical service-account slug (e.g., `analytics-batch`, `billing-worker`, `support-console`, `synthetic-monitor`). |
| `--tenant` / `-t` | Conditional | Tenant UUID; required for tenant-scoped accounts, optional for global operators. |
| `--scopes` / `-s` | Yes | Comma-separated scopes (validated against approved taxonomy). |
| `--lifetime` | Optional | Requested refresh TTL (minutes); bounded by policy defaults. |
| `--output` / `-o` | Optional | Output format (`json`, `text`, `env`); defaults to JSON. |
| `--vault-role` | Optional | Override Vault AppRole ID if multiple identities exist. |
| `--dry-run` | Optional | Validate request without minting token (for CI linting). |
| `--force` | Optional | Bypass duplicate-detection and mint a new token even if an active issuance exists. |

### 3.3 Environment Variables

- `AUTH_CLI_BASE_URL` — AuthService base URL (default `http://localhost:8000`).  
- `AUTH_CLI_VAULT_ADDR` — Vault endpoint (inherited from environment).  
- `AUTH_CLI_VAULT_ROLE_ID` / `AUTH_CLI_VAULT_SECRET_ID` — AppRole credentials (recommended to source from CI secrets).  
- `AUTH_CLI_MTLS_CERT` / `AUTH_CLI_MTLS_KEY` — Optional mTLS client cert/key if Vault proxies require it.  
- `AUTH_CLI_OUTPUT` — Default output format.

## 4. API Contracts

### 4.1 HTTP Endpoint

- `POST /api/v1/auth/service-accounts/issue`
- Authenticated via Vault-signed request JWT or mTLS.
- Request body:

```json
{
  "account": "analytics-batch",
  "tenant_id": "f2a9c0cb-b03a-4b1d-9c7c-8b6d59f3362d",
  "scopes": ["conversations:read"],
  "lifetime_minutes": 43200,
  "fingerprint": "runner-1234"  // optional identifier for auditing
}
```

- Response body:

```json
{
  "refresh_token": "<JWT>",
  "access_token": null,
  "expires_at": "2025-12-06T00:00:00Z",
  "issued_at": "2025-11-06T12:00:00Z",
  "scopes": ["conversations:read"],
  "tenant_id": "f2a9c0cb-b03a-4b1d-9c7c-8b6d59f3362d",
  "kid": "2025-11-01-primary",
  "account": "analytics-batch",
  "token_use": "refresh"
}
```

- Error responses include structured codes (`invalid_scope`, `unauthorized_account`, `tenant_mismatch`, `rate_limited`).

### 4.2 Authentication Strategy

- Staging/production: CLI retrieves short-lived Vault token via AppRole or OIDC workload identity, then uses Vault Transit to sign a request JWT included in the `Authorization` header (`Bearer vault:<signature>`).  
- Local/testing fallback: support mTLS client certs when Vault Transit is unavailable; disabled in higher environments.  
- AuthService verifies the Vault-signed JWT via Transit verification endpoint and checks RBAC (account ↔ tenant permissions).

## 5. Policy & Validation Rules

- Service-account catalog stored in versioned YAML (`app/core/service_accounts.yaml`) loaded at startup; future migration to a persistent store (Postgres + admin tooling) once requirements grow.  
- CLI validates requested scopes against catalog before making API call.  
- AuthService enforces catalog server-side + tenant RBAC.  
- Minimum refresh TTL: 15 minutes; maximum TTL: 30 days unless override approved.  
- Duplicate issuance within active window returns existing token unless `--force` flag provided.  
- Rate limiting: 5 issuance requests per minute per account and global cap of 30/minute; alerts fire when limits trip.
- Replay protection: CLI payloads include nonce/iat/exp; server enforces single-use via Redis-backed nonce cache (in-memory fallback for dev) with ≤5 minute TTL.
- Multi-tenant accounts (e.g., support console) receive a single global refresh token with `tenant_id` omitted; auditing relies on scopes and operational logging.
- Version 1 issues refresh tokens only; CLI will not mint direct access tokens.

## 6. Output & Storage Guidelines

- CLI defaults to JSON output; `--output env` prints `AUTH_REFRESH_TOKEN=...` for pipeline exports.  
- Do not persist refresh tokens to disk by default; encourage piping directly into secret stores (Vault KV, GitHub Actions secrets, etc.).  
- Structured log emitted with `event=service_account_issue`, `account`, `tenant`, `scopes`, `kid`, `request_id`.

## 7. Error Handling & Observability

- CLI exit codes:
  - `0` success  
  - `1` validation error (bad input)  
  - `2` authentication failure (Vault or AuthService)  
  - `3` authorization failure (scope/tenant mismatch)  
  - `4` server error / unexpected
- Metrics exposed in AuthService: `service_account_issuance_total`, `service_account_issue_failures_total`, `service_account_issue_duration_ms`.  
- Alert when failure rate >2% over 10 minutes or when issuance latency exceeds 2s p95.

## 8. Security Considerations

- CLI never logs refresh token contents by default; `--verbose` redacts secrets.  
- Vault credentials retrieved from environment/CI secrets with minimal TTL.  
- Enforce Vault-signed request JWTs in staging/prod; mTLS fallback limited to local/test modes.  
- Rate limit service-account issuance to prevent brute-force or misconfigured jobs; alerts fire when per-account or global caps are exceeded.

## 9. Implementation Checklist

1. Define service-account catalog (YAML/JSON) and loader in `app/core/service_accounts.py`.  
2. Implement AuthService endpoint with RBAC enforcement, audit logging, and metrics.  
3. Build CLI command module (`anything-agents/bin/auth_cli.py`) with Vault integration helpers.  
4. Write unit + contract tests covering successful issuance, validation errors, and authorization failures.  
5. Document operational steps in runbooks (rotation, revocation, emergency kill).  
6. Provide sample pipeline integration (GitHub Actions, Jenkins, etc.) in `docs/security/examples/`.

## 10. Open Questions (post-decision follow-ups)

- Define persistent-store migration plan for service-account catalog (trigger criteria, tooling).  
- Confirm alert destinations (PagerDuty vs. Slack) for rate-limit breaches.  
- Determine backlog item for adding token revocation support to CLI (`auth tokens revoke`).  
- Document support-console operational procedures leveraging global tokens and audit logs.

> Prepared for AUTH-002 kick-off — feedback welcome before implementation locking.
