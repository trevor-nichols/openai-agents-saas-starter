# Milestone: Multi-Provider Secrets Onboarding

- **Status:** Draft (pending approval)
- **Last Updated:** 2025-11-15
- **Owners:** Platform Foundations · Starter CLI Maintainers · Backend Auth Pod
- **Slack Channel:** #proj-secrets-provider

## 1. Why

Our SaaS starter currently hardcodes Vault as the only secrets/signing backend. HashiCorp’s licensing changes plus the desire for cheaper, turnkey options mean operators need alternatives (Infisical, cloud-native stores, managed SaaS). Without first-class support in the Starter CLI and backend, teams either run insecure dev defaults in production or abandon the starter entirely. This milestone unlocks cost-flexible, production-ready secret management without compromising our architecture principles.

## 2. Success Criteria

1. Backend and CLI share a `SecretProvider` abstraction selectable via config/CLI onboarding.
2. Vault dev mode remains the default path and now uses the new abstraction (no regressions).
3. Operators can run `starter_cli secrets onboard` to choose Vault Dev, HCP Vault, Infisical Cloud, or Infisical Self-Host and get working env scaffolding + validation.
4. Documentation (`docs/security`) explains trade-offs, cost tiers, and runbooks for each provider.
5. CI adds at least one smoke check to ensure the onboarding command does not regress (mocked providers acceptable).

## 3. Deliverables by Phase

### Phase 0 — Discovery & Design (ETA: 3 days)
- Audit current Vault wiring across backend + CLI.
- Draft `SecretProvider` interface (methods, data contracts) and review with backend + CLI owners.
- Update architecture diagrams/SNAPSHOT references to note upcoming changes.

### Phase 1 — Abstraction & Registry (ETA: 5 days)
- Implement provider registry + DI hook in backend (`get_secret_provider` dependency).
- Port existing Vault Transit client onto the new interface.
- Mirror registry in Starter CLI; ensure current commands keep working.
- Add configuration keys (`SECRETS_PROVIDER`, provider-specific blocks) to env templates.

### Phase 2 — CLI Onboarding UX (ETA: 4 days)
- Add `starter_cli secrets onboard` with interactive + non-interactive flags.
- Menu covers Vault Dev, HCP Vault, Infisical Cloud, Infisical Self-Host (others stubbed as “coming soon”).
- Each path emits `.env`/`.env.local` snippets and runs a post-setup health check.
- Integration tests mock external APIs (Vault sys/health, HCP, Infisical) to keep CI hermetic.

### Phase 3 — Infisical Integration (ETA: 6 days)
- Implement `InfisicalSecretProvider` (REST client + caching strategy).
- Handle CLI flows: `infisical login`, service-token creation, `infisical run` wrapping.
- Support both SaaS and self-hosted endpoints (configurable base URL).
- Document operational guidance, rate limits, and rotation steps.

### Phase 4 — Hardening & Stretch Providers (ETA: 6 days)
- Add metrics/telemetry for provider selection (opt-in usage stats).
- Ship docs security appendix comparing providers.
- Prepare stubs for cloud-native stores (AWS Secrets Manager, Azure Key Vault) with TODO checklists.
- Finalize milestone review: demo CLI onboarding + backend failover.

## 4. Dependencies & Risks

- **Docs debt:** need to update `docs/security/vault-transit-signing.md` references to point at the new provider overview.
- **CLI UX:** onboarding flow must stay side-effect free on import; ensure new modules respect CLI charter.
- **Testing:** CI must mock external services to avoid leaking real credentials; failure to do so blocks merges.
- **Timeline risk:** Infisical REST API limits or CLI changes could slip Phase 3; mitigate by partnering with Infisical OSS maintainers early.

## 5. Approvals & Next Steps

1. Circulate this milestone with Platform Foundations + Security for sign-off.
2. Once approved, open child issues for each phase in `docs/trackers/ISSUE_TRACKER.md`.
3. Kick off Phase 0 discovery and schedule a design review for the `SecretProvider` interface.

---

## 6. Phase 0 Findings (2025-11-15)

### 6.1 Current Vault Touchpoints
- **Backend:** `app/infrastructure/security/vault.py` exposes `VaultTransitClient` used by `app/services/service_account_bridge.py` and auth routers for signature verification. Settings live under `app/core/config.Settings` (`vault_addr`, `vault_token`, `vault_transit_key`, `vault_verify_enabled`). KV helpers for signing-key storage proxy through `starter_shared.vault_kv`.
- **CLI:** `starter_cli/services/security/signing.py` builds Vault envelopes + signatures; `starter_cli/commands/auth.py` depends on Vault headers; setup wizard validators probe the Transit key; `starter_cli/commands/infra.py` shells into Make targets for dev Vault.
- **Shared:** `starter_shared/config.py` exposes only the Vault-centric settings to the CLI; `starter_shared/vault_kv.py` registers the KV client when `auth_key_storage_backend=secret-manager`.

### 6.2 SecretProvider Protocol (backend + CLI)
Located in new module `api-service/app/domain/secrets.py` (mirrored under `starter_shared/secrets/models.py`):
```python
class SecretProviderProtocol(Protocol):
    async def get_secret(self, key: str, *, scope: SecretScope | None = None) -> str: ...
    async def get_secrets(self, keys: Sequence[str], *, scope: SecretScope | None = None) -> dict[str, str]: ...
    async def sign(self, payload: bytes, *, purpose: SecretPurpose) -> SignedPayload: ...
    async def verify(self, payload: bytes, signature: str, *, purpose: SecretPurpose) -> bool: ...
    async def health_check(self) -> SecretProviderHealth: ...
```
- `SecretScope` (Enum) distinguishes contexts such as `SERVICE_ACCOUNT`, `DATABASE`, `THIRD_PARTY_API`.
- `SecretPurpose` (Enum) captures signing flows (`SERVICE_ACCOUNT_ISSUANCE`, `CLI_BRIDGE`, future entries).
- `SignedPayload` dataclass → `signature: str`, `algorithm: str`, `metadata: dict[str, Any]`.
- `SecretProviderHealth` dataclass → `status: Literal["healthy","degraded","unavailable"]`, `details: dict[str, Any]`.

### 6.3 Config Schema Decisions
- Add `SecretsProviderLiteral` enum with values: `vault_dev`, `vault_hcp`, `infisical_cloud`, `infisical_self_host`.
- Extend `Settings` (and `StarterSettingsProtocol`) with:
  - `secrets_provider: SecretsProviderLiteral = "vault_dev"`.
  - `vault: VaultSettings` (addr/token/transit_key/namespace/verify flag).
  - `infisical: InfisicalSettings` (base_url, service_token, project_id, environment, secret_path, ca_bundle).
- Backend `.env.example` + CLI env templates gain matching keys; validation errors should clearly indicate missing fields for the selected provider.

### 6.4 Provider Registry & DI
- Backend registry module `app/infrastructure/secrets/registry.py` maps enum → provider factory, injects shared dependencies (httpx client, redis nonce store). `get_secret_provider()` FastAPI dependency caches the constructed provider per-process.
- CLI registry `starter_cli/secrets/registry.py` mirrors enum mapping but creates lightweight helpers suitable for command execution (no FastAPI imports).
- Existing Vault client becomes `VaultSecretProvider` that implements the Protocol and wraps `VaultTransitClient` + nonce store.

### 6.5 CLI Onboarding Command
- New command: `starter_cli secrets onboard [--provider ...] [--non-interactive --answers-file path]`.
- Supported choices in Phase 1: `vault_dev` (runs `just vault-up`, captures printed envs), `hcp_vault` (prompts for HCP org/project + service principal, optionally hits HCP API), `infisical_cloud` (runs `infisical login/init`, captures workspace/env IDs), `infisical_self_host` (downloads Infisical compose bundle, runs docker compose up, collects admin token).
- Output artifacts: `.env.local` snippets for backend/frontend, optional CI secret checklist, post-setup validation summary.

### 6.6 Next Steps (Phase 1 Prep)
1. Scaffold `app/domain/secrets.py` + `starter_shared/secrets/models.py` with the Protocol/types above.
2. Introduce config enum + nested settings, updating `StarterSettingsProtocol`.
3. Build registry skeletons and wrap the current Vault implementation without changing behavior.
4. Update docs (`ISSUE_TRACKER` entry BE-007) to reference these concrete deliverables.

## 7. Phase 1 Progress (2025-11-15)

- Added shared `SecretProviderProtocol` + config dataclasses (`starter_shared/secrets/models.py`) and backend re-export (`app/domain/secrets.py`).
- Extended FastAPI settings + CLI bridge to include `SECRETS_PROVIDER`, Vault namespace, and Infisical settings, plus typed `vault_settings`/`infisical_settings` accessors.
- Implemented backend provider registry + `VaultSecretProvider` shim, plus CLI registry stubs (Vault only for now).
- Refactored service-account issuance flows (browser + CLI endpoints) to resolve the provider abstraction instead of `get_vault_transit_client`, preserving Vault behavior while isolating future providers.
- Contract tests now stub the provider registry instead of Vault clients, verifying nonce enforcement and signature validation through the new interface.

## 8. Phase 2 Progress (2025-11-15)

- Added `starter_cli secrets onboard` with shared command plumbing, answer-file support, non-interactive mode, and provider selection menu.
- Vault Dev workflow now guides operators through `just vault-up`, gathers defaults (addr/token/transit key), and prints env snippets + warnings.
- HCP Vault workflow prompts for addr/namespace/token/transit key, emits env entries, and documents follow-up tasks (Transit enablement, `just verify-vault`).
- Infisical Cloud/Self-Host appear in the selector as “coming soon” so UX strings stay stable while backend support is under construction.

## 9. Phase 3 Progress (2025-11-15)

- Implemented `InfisicalSecretProvider` with REST client + TTL cache, using Infisical secrets + HMAC-SHA256 as the signing primitive for service-account payloads.
- Backend registry now resolves Infisical providers for both Cloud and Self-Host enum values; new unit test validates signing/verification.
- CLI onboarding flows collected Infisical inputs (service token, workspace, env, secret path, signing secret) for both Cloud and Self-Host, including optional CA bundle support and API verification.
- Settings + shared config gained `INFISICAL_SIGNING_SECRET_NAME`/`INFISICAL_CACHE_TTL_SECONDS`, ensuring typed parity across backend + CLI.

## 10. Phase 4 Progress (2025-11-15)

- Authored `docs/security/secrets-providers.md` with provider matrix, runbooks, env var cheatsheet, and TODO checklists for AWS/Azure support; linked the existing Vault doc to the new overview.
- Added provider initialization logging inside `app/infrastructure/secrets/registry.py` so ops telemetry captures which provider is active; CLI onboarding already prints provider summaries when finishing.
- Recorded remaining cloud-native work as TODOs in the new doc + milestone notes, keeping BE-007 focused on telemetry/docs hardening before adding more providers.

## 11. Phase 5 Plan — AWS Secrets Manager Integration

**Goal:** Offer a first-party AWS-native option for teams already invested in IAM/KMS, covering both backend signing and CLI onboarding.

- **Config additions**
  - `AWS_REGION`, `AWS_SECRETS_MANAGER_SIGNING_SECRET_ARN`, `AWS_SECRETS_MANAGER_CACHE_TTL_SECONDS`
  - Optional auth sources: `AWS_PROFILE`, `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`/`AWS_SESSION_TOKEN`, or IMDS when running in EC2/ECS/Lambda.
- **Backend provider design**
  - Wrap `boto3` (or `botocore`) client for Secrets Manager and optional KMS.
  - Signing strategy: reuse HMAC flow by storing signing secret value in Secrets Manager. Optional enhancement: support asymmetric KMS keys for future-proofing.
  - Implement `AWSSecretsManagerProvider` with local TTL cache (reuse Infisical pattern) and health checks using `DescribeSecret`.
  - Update registry to resolve `SecretsProviderLiteral.AWS_SM` (new enum value) and wire `SecretProviderHealth` exposures.
- **CLI onboarding**
  - Prompt for AWS auth method (profile vs static keys vs “use instance role”), region, secret ARN/name.
  - Validate by calling `aws secretsmanager get-secret-value` (via boto3) or hitting AWS HTTP endpoints; provide IAM policy snippet if call fails.
  - Emit env snippets plus next steps (e.g., “attach IAM policy allowing secretsmanager:GetSecretValue on ARN XYZ”).
- **Docs & trackers**
  - Expand `docs/security/secrets-providers.md` with AWS section (requirements, IAM policy template, troubleshooting).
  - Update ISSUE_TRACKER entry BE-007 once Phase 5 lands; Phase 6 will mirror for Azure Key Vault.

## 12. Phase 5 Progress (2025-11-15)

- Added `aws_sm` config knobs + shared dataclasses (region, profile/keys, signing secret ARN, cache TTL) across backend + CLI settings.
- Implemented `AWSSecretsManagerClient` and `AWSSecretsManagerProvider` (HMAC via Secrets Manager) plus unit coverage; registry now supports `aws_sm`.
- `starter_cli secrets onboard` gained the AWS workflow (region/ARN/auth selection, AWS probe, env snippet output).
- `docs/security/secrets-providers.md` updated with AWS row, env vars, runbook, and checklist updates.

## 13. Phase 6 Plan — Azure Key Vault Integration

**Goal:** Provide parity for Azure-native shops by reading the signing secret from Key Vault (Secret or Key) and wiring the CLI with service principal / managed identity support.

- **Config additions**
  - `AZURE_KEY_VAULT_URL`, `AZURE_KV_SIGNING_SECRET_NAME`, `AZURE_KV_CACHE_TTL_SECONDS`
  - Auth inputs: `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET` (for service principals) plus optional `AZURE_MANAGED_IDENTITY_CLIENT_ID`.
- **Backend provider**
  - Use `azure-identity` + `azure-keyvault-secrets` to load secrets; default to `DefaultAzureCredential` so managed identities just work.
  - Mirror the HMAC strategy used by Infisical/AWS (secret value in Key Vault).
  - Health check: `client.get_secret` or `client.get_secret_properties`.
- **CLI onboarding**
  - Prompt for Key Vault URL, signing secret name, auth method (service principal vs managed identity). Validate by calling Key Vault via the Azure SDK.
  - Emit env vars and highlight required Azure role assignments (`Key Vault Secrets User` or `Secrets Officer`).
- **Docs/tests**
  - Expand `docs/security/secrets-providers.md` with Azure section (setup steps, RBAC).
  - Unit tests using `azure.core.pipeline.policies` mocks or simple fake client.
  - Update milestone + issue tracker after landing.

## 14. Phase 6 Progress (2025-11-15)

- Added Azure KV config + shared dataclasses (vault URL, secret name, tenant/app creds, managed identity client ID, cache TTL) and exposed `azure_settings`.
- Implemented `AzureKeyVaultClient` + `AzureKeyVaultProvider` (HMAC via Key Vault secrets) with unit tests; registry now routes `azure_kv`.
- CLI onboarding menu now includes Azure; workflow prompts for vault URL, secret, auth method (SPN vs managed identity), validates via Azure SDK, and emits env snippets.
- `docs/security/secrets-providers.md` updated with Azure rows, env vars, runbook, and checklist changes.

## 15. Phase 7 Progress (2025-11-15)

- Added opt-in telemetry controls: backend `ENABLE_SECRETS_PROVIDER_TELEMETRY` toggles logging of provider initialization, and the CLI honors `STARTER_CLI_TELEMETRY_OPT_IN` to emit anonymized onboarding events.
- Updated `docs/security/secrets-providers.md` to explain telemetry toggles and privacy stance.
- **Config additions**
- `AZURE_KEY_VAULT_URL`, etc...
