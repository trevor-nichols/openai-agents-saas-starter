# Starter Contracts

Shared, import-safe contracts and helpers used by both the FastAPI backend and the Starter Console. This package keeps configuration, secrets, storage, logging, and key-management logic decoupled from app code so the console can run without importing the server stack. Concrete cloud SDK clients live in `starter_providers`.

## What this package provides
- Provider-neutral contracts for secrets and storage (protocols, health models, config dataclasses).
- External provider validation (OpenAI, Stripe, Resend, hosted web search parity).
- A lazy settings bridge (`StarterSettingsProtocol` + `get_settings`) so tooling can consume backend config without importing `app.core.settings` at import time.
- Ed25519 key generation, JWKS materialization, and pluggable key storage (file or secret manager).
- Vault KV v2 secret-manager client for key storage.
- Shared structured logging primitives: JSON formatter, context propagation, event helper, and sink configuration for stdout/file/Datadog/OTLP.
- Repo-root path helpers for runtime artifacts (`var/log`, generated configs, etc.).
- Versioned doctor schema (`doctor_v1.json`) used by CLI diagnostics.

## Where it is used
- **Backend (FastAPI):** Implements concrete providers and key storage using these protocols; the backend `Settings` class satisfies `StarterSettingsProtocol`. Logging config + sinks are reused from this package.
- **Starter Console:** Reads backend settings via `get_settings()`, performs provider parity checks, manages auth keys (file or secret-manager), and emits doctor reports against the shared schema.
- **Starter Providers:** Implements the concrete SDK clients for secrets/storage that conform to these contracts.
- **Frontend (Next.js):** Does not import this package directly; benefits indirectly from consistent backend/CLI configuration.

## Key modules
- `config.py`: Narrow settings protocol + lazy loader for backend settings.
- `secrets/models.py`: Enums, dataclasses, and protocol for secrets providers (Vault, Infisical, AWS, Azure).
- `storage/models.py`: Enums, dataclasses, and protocol for object storage providers (MinIO, S3, GCS, Azure Blob).
- `provider_validation.py`: Shared validation and parity enforcement for external providers.
- `keys.py`: Ed25519 key lifecycle, JWKS projection, and storage adapters (file, secret manager).
- `vault_kv.py`: Vault KV client + registrar for secret-manager key storage.
- `observability/logging/*`: Structured logging config, context helpers, event emitter, and sink builders.
- `paths.py`: Repo-root path resolution helpers.
- `doctor_v1.json`: JSON schema for CLI doctor output.

## Boundaries and guarantees
- Import-safe by design: no direct imports of `app.*` or `starter_console.*` at module import time.
- `get_settings()` lazily imports `app.core.settings` from `apps/api-service/src` when called.
- `tests/test_import_boundaries.py` enforces package boundaries and prevents accidental coupling.
- Keep changes backwards compatible for shared consumers (backend + console + providers).

## Extending safely
- Add new settings only via `StarterSettingsProtocol` and wire them in the backend `Settings` class.
- When adding provider-specific features, update both the contracts **and** `provider_validation.py` so CLI and backend stay aligned.
- For new diagnostics, version schemas (e.g., `doctor_v2.json`) instead of breaking the existing one.

## Development
- `cd packages/starter_contracts && hatch run lint`
- `cd packages/starter_contracts && hatch run typecheck`
- `cd packages/starter_contracts && hatch run test`
- Ruff formatting: `cd packages/starter_contracts && hatch run format`
- Python version: 3.11 (see `pyproject.toml`); package ships `py.typed`.
