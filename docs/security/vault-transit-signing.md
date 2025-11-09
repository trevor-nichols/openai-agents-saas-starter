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
