# Vault Transit Signing Integration Plan

**Status:** Draft for implementation  
**Last Updated:** 2025-11-06  
**Owners:** Backend Auth Pod · Platform Security Guild

---

## 1. Goal

Enable the AuthService CLI and backend to authenticate service-account issuance requests using Vault Transit–signed JWTs. This replaces static tokens and aligns with our security posture for staging/production.

## 2. Handshake Overview

```
CLI
 ├─ Obtain Vault AppRole token (or workload OIDC) -> VAULT_TOKEN
 ├─ Build request payload:
 │     {
 │       "iss": "vault-transit",
 │       "aud": ["auth-service"],
 │       "sub": "service-account-cli",
 │       "account": "<account>",
 │       "tenant_id": "<tenant or null>",
 │       "scopes": ["..."],
 │       "nonce": "<uuid>",
 │       "iat": <timestamp>,
 │       "exp": <timestamp + 5m>
 │     }
 ├─ Send payload to Vault Transit sign endpoint:
 │     POST /v1/transit/sign/auth-service
 │     body: {"input": base64url(payload_json)}
 ├─ Receive signature (base64) -> construct Authorization header:
 │     Authorization: Bearer vault:<signature>
 └─ Call AuthService issuance endpoint with original parameters + header

AuthService
 ├─ Extract Authorization header
 ├─ Verify signature via Vault Transit verify endpoint:
 │     POST /v1/transit/verify/auth-service with payload + signature
 ├─ Validate JWT claims (iss, aud, exp, nonce uniqueness, account match)
 ├─ Proceed with service-account issuance logic
```

### 2.1 Local dev quickstart (Docker + Make)

To exercise this flow without provisioning a real Vault cluster, use the new dev-only helper:

1. `make vault-up` – starts `hashicorp/vault` in dev mode on `http://127.0.0.1:18200`, enables the Transit engine, and prints the env vars you need to export (`VAULT_ADDR`, `VAULT_TOKEN`, `VAULT_TRANSIT_KEY`, `VAULT_VERIFY_ENABLED=true`).
2. Update your shell or `.env.local` with those exports so both FastAPI and the Starter CLI talk to the dev signer.
3. Run the API (`make api`) and then `make verify-vault` to execute `starter_cli auth tokens issue-service-account` against the running backend. That command uses the Vault dev signer and will fail if the signature or backend wiring regresses.
4. When finished, `make vault-down` tears the container down; `make vault-logs` tails the Vault output for troubleshooting.

> ⚠️ This Compose stack is for local testing only. The dev image stores everything in-memory, has no TLS, and uses a static root token. Production/staging deployments must still bring a hardened Vault/KMS setup per the remainder of this document.

### 2.2 Browser issuance bridge

To keep Vault credentials off the browser entirely, `/api/v1/auth/service-accounts/browser-issue` now acts as the signing bridge:

- Tenant admins (or platform operators with override headers) call this endpoint with the same fields as `/service-accounts/issue` plus a required `reason` string.
- FastAPI validates the session, builds the Vault Transit payload server-side, signs it via the configured Vault client, and immediately calls `auth_service.issue_service_account_refresh_token`. The signature never leaves the server, so browsers can’t replay or tamper with it.
- The endpoint returns the usual `ServiceAccountTokenResponse`, so the frontend can show the “copy once” UI just like the CLI. Errors from the signer (missing Vault config, rate limits, catalog issues) map to the same HTTP codes as the CLI route (400/429/503).
- Tenant admins are hard-scoped to their current tenant; the backend automatically injects the tenant ID into the Vault payload and rejects any cross-tenant attempts with HTTP 403. Platform operators with override headers remain exempt so they can troubleshoot customers.
- All bridge calls are logged via `service_account_browser_issue` events (stage `sign` + `issue`) with the account, tenant, actor, and justification for auditing.

The original `/service-accounts/issue` route (requiring `Authorization: Bearer vault:<signature>`) remains available for headless automation via the CLI. In other words: browsers go through the bridge, automation keeps using Vault-signed HTTP requests.

For cases where we explicitly need to exercise the canonical HTTP endpoint from the web tier (e.g., to replay a Vault-signed request captured from CI), the Next.js frontend now exposes `/app/api/auth/service-accounts/issue`. That proxy requires authenticated human sessions plus the `X-Vault-Authorization`/`X-Vault-Payload` headers obtained from Vault Transit, then forwards them verbatim to FastAPI `/api/v1/auth/service-accounts/issue`.

## 3. Request & Response Formats

### 3.1 CLI Payload (pre-signing JSON)

```json
{
  "iss": "vault-transit",
  "aud": ["auth-service"],
  "sub": "service-account-cli",
  "account": "analytics-batch",
  "tenant_id": "f2a9c0cb-b03a-4b1d-9c7c-8b6d59f3362d",
  "scopes": ["conversations:read"],
  "nonce": "5d0463f3-6df0-4e29-b10f-7aa5bfa16b1b",
  "iat": 1767724800,
  "exp": 1767725100
}
```

### 3.2 Authorization Header

```
Authorization: Bearer vault:<signature>
X-Vault-Payload: <base64url(payload_json)>
```

- `vault:<signature>` – base64url signature returned by Transit.  
- `X-Vault-Payload` – base64url of the unsigned payload so the server can verify without rehydrating request JSON.

### 3.3 Transit API Calls

- **Sign** (CLI):
  - `POST /v1/transit/sign/auth-service`
  - body: `{"input": "<base64url(payload_json)>", "signature_algorithm": "sha2-256"}`
- **Verify** (AuthService):
  - `POST /v1/transit/verify/auth-service`
  - body: `{"input": "<base64url(payload_json)>", "signature": "<signature>"}`  

Vault returns `{"data": {"valid": true}}` when verification succeeds.

## 4. Server-side Helpers

- `app/infrastructure/security/vault.py`
  - `class VaultTransitClient`: wraps HTTP calls to Vault (sign/verify).  
  - `verify_signature(payload_b64: str, signature: str) -> bool`.  
  - Configurable via settings: `vault_addr`, `vault_token`, path, timeout.
- `app/infrastructure/security/nonce_store.py`
  - Provides Redis-backed nonce caching (tests rely on fakeredis to avoid external dependencies).  
  - `check_and_store(nonce, ttl_seconds)` ensures each CLI payload nonce is single-use with ≤5 minute TTL.
- `app/core/config.py`
  - Add settings: `vault_addr`, `vault_token`, `vault_transit_key`, `vault_verify_enabled` (feature flag for local).
- Dependency injection:
  - Provide `get_vault_client()` for FastAPI dependencies.  
  - For tests, supply a mock client with deterministic responses.

## 5. CLI Adjustments

- Extend CLI to:
  - Fetch payload metadata (account, tenant, scopes) and produce signing payload.  
  - Call Vault Transit sign endpoint using `AUTH_CLI_VAULT_ADDR`, `AUTH_CLI_VAULT_ROLE_ID`, `AUTH_CLI_VAULT_SECRET_ID`.  
  - Populate `Authorization` and `X-Vault-Payload` headers.
- For local/development:
  - Feature flag `AUTH_CLI_DEV_AUTH_MODE=local` bypasses Transit and uses `Bearer dev-local`.

## 6. Testing Strategy

- Introduce `FakeVaultTransitClient` in tests returning configurable `valid` responses.  
- Contract tests in `tests/contract` verifying:
  - valid signature -> 201 response  
  - invalid signature -> 401  
  - expired payload (`exp` past) -> 401  
  - mismatched account in payload vs. body -> 400  
- CLI integration test using `responses`/`httpx.MockTransport` to simulate Vault responses.

## 7. Sequence Diagram (Staging/Prod)

```
CLI                               Vault                         AuthService
 |---login (AppRole/OIDC)--------->|                               |
 |<--token-------------------------|                               |
 |---sign payload (POST /sign)---->|                               |
 |<--signature---------------------|                               |
 |---POST /service-accounts/issue------------------------------->  |
 |   Authorization: Bearer vault:<signature>                      |
 |   X-Vault-Payload: <payload_b64>                               |
 |                                                                |
 |                               |---POST /verify-------------->  |
 |                               |   input/payload, signature     |
 |                               |<--{valid:true}---------------- |
 |                                                                |
 |<--201 ServiceAccountTokenResponse------------------------------|
```

## 8. Implementation Tasks

1. Add Vault configuration settings (`vault_addr`, `vault_token`, `vault_transit_key`, flags).  
2. Implement `VaultTransitClient` with `verify_signature`.  
3. Update auth router to:
   - Read `X-Vault-Payload` header.  
   - Verify via client; validate nonce/exp/account vs. body.  
4. Extend CLI to sign payload via Transit and attach headers.  
5. Add tests (unit + contract + CLI).  
6. Update docs/runbooks with operational guidance.

## 9. Open Questions

- Nonce storage to prevent replay: resolved — use Redis everywhere (tests rely on fakeredis to avoid external dependencies).  
- Should CLI cache Transit signatures per run for retries?  
- How to rotate Transit key names (include `key_version` header or fetch from settings)?

> Once approved, we’ll implement using this plan, coordinating with security for key provisioning and IAM policies.
