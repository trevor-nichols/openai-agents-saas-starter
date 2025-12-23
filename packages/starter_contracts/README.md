# Starter Contracts

Shared, import-safe contracts and helpers that both the FastAPI backend and the Starter CLI rely on. This package keeps configuration, secrets, storage, and key-management logic decoupled from app code so the CLI can run without importing the server stack. Concrete cloud SDK clients live in `starter_providers`.

## What this package does
- Defines provider-neutral contracts for secrets and storage (`secrets/`, `storage/`) plus health and signing interfaces. (Concrete SDK clients live in `starter_providers`.)
- Validates external provider setup (`provider_validation.py`) for OpenAI, Stripe, Resend, and web search parity.
- Bridges backend settings into the CLI without importing `app.core.settings` eagerly (`config.py`).
- Manages Ed25519 auth key generation, JWKS materialization, and pluggable key storage backends (`keys.py`).
- Ships a Vault KV client and registrar for secret-manager key storage (`vault_kv.py`).
- Publishes the CLI doctor report schema used by diagnostics (`doctor_v1.json`).

## Where it is used
- Backend (FastAPI): Implements concrete providers and key storage using these protocols; the backend `Settings` class satisfies `StarterSettingsProtocol`.
- Starter CLI: Reads backend settings via `get_settings()`, performs provider parity checks, manages auth keys (file or secret-manager), and emits doctor reports against the shared schema.
- Frontend (Next.js): Does not import this package directly; benefits indirectly from consistent backend/CLI configuration.

## Key modules
- `config.py`: Narrow protocol + lazy loader for backend settings consumed by the CLI.
- `secrets/models.py`: Enums/dataclasses/protocol for secret providers, signing, scopes, and health.
- `storage/models.py`: Enums/dataclasses/protocol for object storage providers, presigned URLs, and health.
- `provider_validation.py`: Shared validation and parity enforcement for external providers.
- `keys.py`: Ed25519 key lifecycle, JWKS projection, and storage adapters (file, secret-manager via registered client).
- `vault_kv.py`: Vault KV client + `configure_vault_secret_manager` registrar for secret-manager setups.
- `doctor_v1.json`: JSON schema for CLI doctor output.

## Usage and boundaries
- Depend on these protocols and helpers from both backend and CLI; avoid importing backend application modules inside this package.
- If adding a new provider, extend the appropriate models and update validations to keep CLI and backend behavior aligned.
- Key storage backends are selected via `auth_key_storage_backend` (`file` or `secret-manager`); register a secret-manager client before use.
- Keep imports acyclic: `tests/test_import_boundaries.py` enforces the package stays free of app-level dependencies.

## Development
- Optional tooling via Hatch (preferred): `hatch run lint`, `hatch run typecheck`, `hatch run test`.
- Ruff formatting: `hatch run format`.
- Python version: 3.11 (see `pyproject.toml`); package is `py.typed`.

## Extending safely
- Add new settings only through the `StarterSettingsProtocol` surface so the CLI remains import-safe.
- When adding provider-specific features, ensure both validation and health contracts reflect the change.
- For new diagnostics, version doctor schemas (`doctor_v2.json`, etc.) instead of breaking the existing one.
