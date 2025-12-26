# Contracts Package (`starter_contracts`)

Source of truth for shared config/secrets/storage/key/logging contracts consumed by:
- Backend (`apps/api-service/...`)
- Starter Console (`packages/starter_console/...`)
- Repo tools (`tools/cli/verify_env_inventory.py`), tests, and contract snapshots.

## Allowed import graph
- Only the surfaces above should import `starter_contracts.*`.
- `starter_contracts` must **not** import `app.*` (backend) or `starter_console.*` at module import time.
- Import-time side effects are forbidden; `get_settings()` is lazy and should only fire when called.
- Cloud SDK clients now live in `starter_providers`; contracts must remain dependency-light and not import provider SDKs.

## Modules
- `config`: `StarterSettingsProtocol`, `get_settings()` lazy loader for backend settings.
- `keys`: Ed25519 key material, JWKS materialization, file/secret-manager adapters.
- `provider_validation`: Shared OpenAI/Stripe/Resend/web-search parity validation helpers.
- `secrets.models`: Enums + dataclasses + protocols for secret providers (Vault, Infisical, AWS SM, Azure KV).
- `storage.models`: Enums + dataclasses + protocols for object storage providers (MinIO, S3, GCS, Azure Blob).
- `observability/logging`: Structured JSON logging config, context helpers, event emitter, and sink builders.
- `paths`: Repo-root path resolution helpers used by logging/config tooling.
- `vault_kv`: Minimal Vault KV v2 client + registration helper when keys live in a secret manager.
- `doctor_v1.json`: JSON schema for CLI doctor output.

## Related package: `starter_providers`
- Houses concrete SDK clients for AWS Secrets Manager, Azure Key Vault, and Infisical.
- May depend on provider SDKs, but must not import `app.*` or `starter_console.*` at module import time.
- Both backend and console should import SDK clients from `starter_providers.secrets.*`.

## Snapshots (drift blockers)
- `docs/contracts/settings.schema.json`: JSON Schema snapshot of `app.core.settings.Settings`.
- `docs/contracts/provider_literals.json`: Enumerated values for shared secret/provider/sign-up literals.
- Tests enforce snapshots: `apps/api-service/tests/unit/test_contract_schemas_snapshot.py`.

### Updating snapshots
Only update when you intentionally change settings or provider enums:

```bash
# Ensure local path to backend wins over site-packages 'app'
PYTHONPATH=apps/api-service \
python - <<'PY'
from pathlib import Path
from typing import get_args
import json, sys
sys.path.insert(0, 'apps/api-service')
from app.core.settings import Settings, SignupAccessPolicyLiteral
from starter_contracts.secrets.models import SecretProviderStatus, SecretPurpose, SecretScope, SecretsProviderLiteral

def canonical(obj):
    if isinstance(obj, dict):
        return {k: canonical(v) for k, v in sorted(obj.items())}
    if isinstance(obj, list):
        return [canonical(v) for v in obj]
    return obj

root = Path('.').resolve()
contracts = root / 'docs' / 'contracts'
contracts.mkdir(parents=True, exist_ok=True)
(contracts / 'settings.schema.json').write_text(json.dumps(canonical(Settings().model_json_schema()), indent=2, sort_keys=True) + '\n')
enums = {
    'secrets_provider_literal': sorted(item.value for item in SecretsProviderLiteral),
    'secret_scope': sorted(item.value for item in SecretScope),
    'secret_purpose': sorted(item.value for item in SecretPurpose),
    'secret_provider_status': sorted(item.value for item in SecretProviderStatus),
    'signup_access_policy_literal': sorted(get_args(SignupAccessPolicyLiteral)),
}
(contracts / 'provider_literals.json').write_text(json.dumps(enums, indent=2, sort_keys=True) + '\n')
PY
```

Commit the updated JSON along with the change that necessitated it.

## Tests enforcing boundaries
- `starter_contracts/tests/test_import_boundaries.py`: ensures contracts don't pull backend/console modules on import and are only used from approved packages.
- `apps/api-service/tests/unit/test_contract_schemas_snapshot.py`: freezes settings + enum schemas.
