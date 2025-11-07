# Ed25519 Key Rotation Playbook

**Status:** Source-of-truth for rotation ops  
**Last Updated:** 2025-11-07  
**Owners:** Backend Auth Pod · Platform Security Guild

---

## 1. Purpose
Maintain continuous trust in the Anything Agents signing infrastructure by rotating Ed25519 key material on a predictable cadence, documenting where keysets live, and proving that freshly generated keys can issue/verify JWTs before promotion.

- Access tokens and refresh tokens are signed by the "active" Ed25519 key.
- A "next" key must always be staged so we can fail over instantly.
- Keysets are stored via the configured backend (`AUTH_KEY_STORAGE_BACKEND=file|secret-manager`).

## 2. Prerequisites
1. **Environment**
   - `AUTH_KEY_STORAGE_BACKEND=file` (default) with `AUTH_KEY_STORAGE_PATH` pointing to a secure, access-controlled location (e.g., `var/keys/keyset.json` on a sealed volume), **or**
   - `AUTH_KEY_STORAGE_BACKEND=secret-manager` with `AUTH_KEY_SECRET_NAME` and Vault/AppRole credentials configured.
2. **CLI access** – Install the auth CLI via `pip install -e .` or use `hatch run auth-cli ...`.
3. **Backups enabled** – Before every rotation, copy the existing keyset artifact to an encrypted backup bucket or rely on secret-manager versioning.
4. **Environment variables** – Export `AUTH_KEY_STORAGE_*` and, when using Vault, ensure `VAULT_ADDR`/`VAULT_TOKEN` are populated so the CLI can load/save keysets.

## 3. Rotation Workflow
### Step 0 – Snapshot the Current Keyset
```bash
hatch run auth-cli jwks print > /tmp/jwks-before.json
cp $AUTH_KEY_STORAGE_PATH /secure/backups/keyset-$(date +%Y%m%d%H%M).json
```
Retain the fingerprint + kid list in your change record.

### Step 1 – Stage the Next Key
```bash
hatch run auth-cli keys rotate
```
- When an active key already exists, this command creates/updates the **next** slot.
- The CLI output includes the new kid; record it under the change ticket.
- If Vault/secret manager is configured, the CLI writes directly to that backend.

### Step 2 – Validate the Staged Key
1. Print JWKS and confirm the new kid appears alongside the current active key:
   ```bash
   hatch run auth-cli jwks print | jq '.keys[].kid'
   ```
2. Hit `/metrics` (optional) to confirm `jwks_requests_total` increments and no signer errors are reported.
3. (Staging) Run the automated smoke test `pytest tests/unit/test_keys_cli.py -k rotation_smoke` or execute the CLI-based check below:
   ```bash
   python - <<'PY'
   from app.core.security import get_token_signer, get_token_verifier
   payload = {"sub": "user:rotation-precheck", "scope": "conversations:read", "token_use": "access"}
   signed = get_token_signer().sign(payload)
   get_token_verifier().verify(signed.primary.token)
   print("verified", signed.primary.kid)
   PY
   ```

### Step 3 – Promote a New Active Key
Once staging smoke tests pass, promote by generating a fresh key in the **active** slot:
```bash
hatch run auth-cli keys rotate --activate-now
```
- The previous active key automatically moves to the retired list.
- The CLI prints the promoted kid; copy this into the rotation log.
- Production consumers will begin receiving tokens signed by the new kid immediately.

### Step 4 – Restage the Next Key
Always leave the "next" slot populated so future promotions can happen without delay:
```bash
hatch run auth-cli keys rotate
```
Repeat the validation from Step 2 for the new next kid.

### Step 5 – Update Audit Artifacts
- Attach the CLI outputs, JWKS fingerprints, and `/metrics` screenshots to the rotation ticket.
- Note the UTC timestamps for staging, promotion, and validation.
- If using Vault, ensure the secret version number is recorded (e.g., via `vault kv metadata get`).

## 4. Rollback / Emergency Procedures
1. **Detected issue** (e.g., verification failures) → switch services to the prior keyset backup:
   - Restore the previous keyset file or secret-manager version.
   - Redeploy pods to pick up the reverted keyset.
2. Issue a fresh rotation when the incident is resolved so you are not running on stale material.
3. Document the rollback in the audit trail with root-cause notes.

## 5. Change Management Checklist
- [ ] Backup existing keyset and JWKS output.
- [ ] Run `auth-cli keys rotate` (stage next) and record kid.
- [ ] Verify JWKS + smoke test on staging.
- [ ] Run `auth-cli keys rotate --activate-now` to promote, record kid.
- [ ] Run smoke test / contract tests (automated in CI via `tests/unit/test_keys_cli.py::test_key_rotation_smoke_sign_and_verify`).
- [ ] Run `auth-cli keys rotate` again to repopulate next slot and log new kid.
- [ ] Update ticket with metrics, timestamps, and confirmation from monitoring.

Following this playbook keeps the EdDSA trust chain auditable and ensures every rotation is tied to explicit verification steps.
