# Starter Providers

Concrete cloud SDK clients shared across the FastAPI backend and the Starter Console. This package hosts dependency-heavy provider integrations so `starter_contracts` can remain import-safe and lightweight.

## What this package provides
- AWS Secrets Manager client (`boto3` wrapper)
- Azure Key Vault client (`azure-identity` + `azure-keyvault-secrets`)
- Infisical API client (`httpx`)

## Where it is used
- **Backend (FastAPI):** Wires secrets providers and storage implementations to these clients.
- **Starter Console:** Uses the same SDK clients during secrets onboarding and validation.
- **Starter Contracts:** Defines the provider protocols/configs that these clients satisfy.

## Module map
- `starter_providers/secrets/aws_client.py`: `AWSSecretsManagerClient`
- `starter_providers/secrets/azure_client.py`: `AzureKeyVaultClient`
- `starter_providers/secrets/infisical_client.py`: `InfisicalAPIClient`
- `starter_providers/secrets/__init__.py`: public re-exports

## Boundaries
- This package must not import `app.*` or `starter_console.*` at module import time.
- Provider clients are thin and side-effect free at import; network calls occur only on method invocation.

## Development
- `cd packages/starter_providers && hatch run lint`
- `cd packages/starter_providers && hatch run typecheck`
- `cd packages/starter_providers && hatch run test`
- Ruff formatting: `cd packages/starter_providers && hatch run format`
- Python version: 3.11 (see `pyproject.toml`); package ships `py.typed`.

## Related docs
- `docs/security/secrets-providers.md`
- `docs/ops/provider-parity.md`
- `packages/starter_contracts/README.md`
