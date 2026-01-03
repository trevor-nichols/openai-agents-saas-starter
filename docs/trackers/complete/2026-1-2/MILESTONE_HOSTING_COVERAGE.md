<!-- SECTION: Metadata -->
# Milestone: Hosting Coverage Expansion

_Last updated: 2026-01-02_  
**Status:** Completed  
**Owner:** Platform Foundations  
**Domain:** Infra  
**ID / Links:** [TBD], [docs/ops/hosting-overview.md], [docs/ops/hosting-aws.md], [docs/ops/hosting-azure.md], [docs/ops/container-deployments.md], [docs/ops/setup-wizard-presets.md], [docs/security/secrets-providers.md], [ops/infra/aws], [ops/infra/azure], [.github/workflows/build-images.yml]

---

<!-- SECTION: Objective -->
## Objective

Provide production-grade, modular deployment blueprints for the most common hosting environments (AWS, Azure, GCP, Kubernetes, and single-server/VPS) while keeping a consistent env contract and minimal coupling to application code, so any developer can clone and deploy with clear, defensible architecture.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- GCP reference blueprint exists and aligns with the AWS/Azure contract (compute, DB, cache, storage, secrets).
- Kubernetes deployment option exists (Helm chart or manifests) with the same env contract and clear separation of API, web, and worker roles.
- Production-grade single-server deployment exists (Compose + reverse proxy with TLS) with documented secrets and backup guidance.
- Docs updated to include GCP/K8s/VPS runbooks and a consolidated “deployment options” page.
- CI validates all new infra directories (terraform fmt/validate, helm lint/template, compose config).
- Trackers updated and the milestone archived on completion.

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Add `ops/infra/gcp` Terraform blueprint (Cloud Run or equivalent; Cloud SQL, Memorystore, GCS, Secret Manager for runtime env injection).
- Add Kubernetes deployment option under `ops/k8s` or `ops/charts` (Helm preferred).
- Add production single-server deployment under `ops/compose` (reverse proxy + TLS + restart policies + backups).
- Normalize provider variable names and env mappings across AWS/Azure/GCP/K8s/Compose.
- Add a GCP Secret Manager provider in the backend + console and set it as the default for GCP.
- Update docs and runbooks to reflect new options.
- Extend CI to validate new infra artifacts.

### Out of Scope
- Automatic `terraform apply` in CI (should remain opt-in and manual).
- Advanced platform-specific features (service mesh, zero-trust networking, custom ingress controllers).
- Multi-region or multi-tenant infrastructure topologies.
- Managed SSO provisioning beyond what the console already supports.

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Shared contract + GCP/K8s/VPS design decisions locked. |
| Implementation | ✅ | `ops/infra/aws`, `ops/infra/azure`, and `ops/infra/gcp` complete; K8s chart + runbook added; VPS compose + proxy + runbook added. |
| Tests & QA | ⚠️ | CI validates terraform + Helm + compose config; workflows need green runs. |
| Docs & runbooks | ✅ | GCP + K8s + VPS runbooks published. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- **Reference shape today:** containerized API + web with managed Postgres, Redis, object storage, and secrets provider. AWS uses ECS/Fargate + RDS + ElastiCache + S3 + Secrets Manager; Azure uses Container Apps + Postgres Flexible Server + Azure Cache + Blob + Key Vault; GCP uses Cloud Run + Cloud SQL + Memorystore + GCS + Secret Manager.
- **Secrets posture:** hosted environments expect secret-manager-backed key storage (`AUTH_KEY_STORAGE_BACKEND=secret-manager`), with the provider chosen via `SECRETS_PROVIDER` and `AUTH_KEY_STORAGE_PROVIDER`.
- **Console presets:** setup wizard supports `aws`, `azure`, `gcp`, and `other` presets with Terraform blueprints for AWS/Azure/GCP.
- **Design requirement:** keep infra definitions modular, DRY, and aligned to a shared env contract so provider additions do not leak into app logic.

### Coverage Gap Matrix

| Deployment target | Current state | Infra present | Gap |
| --- | --- | --- | --- |
| AWS (ECS/Fargate) | Supported | `ops/infra/aws` | None |
| Azure (Container Apps) | Supported | `ops/infra/azure` | None |
| GCP (Cloud Run/GKE) | Supported (Cloud Run) | `ops/infra/gcp` | None |
| Kubernetes (portable) | Supported | `ops/charts/starter` | None |
| Single-server/VPS | Supported | `ops/compose/docker-compose.prod.yml` | None |
| Infra CI validation | Validation configured | `.github/workflows/build-images.yml` | Awaiting green runs |

---

<!-- SECTION: Design Doc -->
## Design Doc: Hosting Coverage Expansion

### Design Goals
- **Single contract, many targets:** a shared env + secret contract across AWS/Azure/GCP/K8s/VPS.
- **Minimal coupling:** infrastructure is responsible for wiring runtime config; app code remains unchanged.
- **Predictable defaults:** hosted presets keep cloud-native services as defaults, but allow overrides.
- **Production-first:** secure networking, managed databases, and secret-manager-backed signing/key storage.

### Locked Decisions (2026-01-02)
- **GCP compute default:** Cloud Run; GKE Autopilot documented as an advanced/optional path.
- **GCP secrets default:** implement a native GCP Secret Manager provider (`gcp_sm`) in backend + console and use it by default for GCP.
- **Kubernetes secrets default:** External Secrets Operator; Secrets Store CSI driver documented as optional.

### Shared Infra Contract (Canonical Inputs)

These inputs are the contract between infrastructure and the app. New targets must adhere to them
unless explicitly documented.

| Category | Key | Description | Notes |
| --- | --- | --- | --- |
| Identity | `project_name` | Base name for resources | Matches AWS/Azure pattern |
| Identity | `environment` | `dev` / `staging` / `prod` | Used for production safety checks |
| Images | `api_image` | API container image | Required |
| Images | `web_image` | Web container image | Required |
| Images | `worker_image` | Billing retry worker image | Optional; defaults to `api_image` if omitted |
| URLs | `api_base_url` | Public API URL for web | Optional; defaults to platform URL |
| URLs | `app_public_url` | Public web URL | Optional; defaults to platform URL |
| Secrets | `secrets_provider` | App secrets provider | Must be one of supported providers |
| Secrets | `auth_key_storage_provider` | Key storage provider | Defaults to `secrets_provider` |
| Secrets | `auth_key_secret_name` | Keyset secret name/path | Required for hosted environments |
| Env | `api_env` | Non-sensitive API env vars | Must exclude `DATABASE_URL`, `REDIS_URL` |
| Env | `web_env` | Non-sensitive web env vars | Optional |
| Secrets | `api_secrets` | Map of API env → secret ref | Must include `DATABASE_URL`, `REDIS_URL` |
| Secrets | `web_secrets` | Map of web env → secret ref | Optional |
| Storage | `storage_provider` | `s3` / `azure_blob` / `gcs` / `minio` | Must align to target |
| Storage | `storage_bucket_name` | Bucket/container name | Provider-specific naming rules |

### Canonical Outputs

Each infra target should emit the same core outputs to keep runbooks predictable:

| Output | Description |
| --- | --- |
| `api_url` | Public API URL |
| `web_url` | Public web URL |
| `storage_bucket` | Bucket/container name (or ID) |
| `database_endpoint` | Database host/endpoint |
| `redis_endpoint` | Redis hostname/endpoint |

### GCP Terraform Blueprint (proposed structure)

Location: `ops/infra/gcp`

```
ops/infra/gcp/
  main.tf
  versions.tf
  variables.tf
  outputs.tf
  locals.tf
  network.tf            # VPC + subnets + Serverless VPC Access connector
  cloud_run.tf          # api/web/worker services + IAM
  cloud_sql.tf          # Cloud SQL Postgres + users + private IP
  redis.tf              # Memorystore Redis
  storage.tf            # GCS bucket
  secrets.tf            # Secret Manager wiring + access
  iam.tf                # Service accounts + roles
  README.md             # Required vars + quickstart
```

**Design notes**
- Prefer Cloud Run as the default compute target for parity with ECS/Container Apps.
- Use private IP for Cloud SQL + VPC connector for Cloud Run access.
- Default secrets provider for GCP deployments is `gcp_sm`, aligned with the hosting presets and Secret Manager integration.
- Registry: support Artifact Registry and GHCR via `registry_*` variables (same pattern as AWS/Azure).

### Kubernetes (Helm) Layout

Location: `ops/charts/starter`

```
ops/charts/starter/
  Chart.yaml
  values.yaml
  values.dev.yaml
  values.prod.yaml
  templates/
    _helpers.tpl
    api-deployment.yaml
    web-deployment.yaml
    worker-deployment.yaml
    api-service.yaml
    web-service.yaml
    ingress.yaml
    hpa.yaml
    serviceaccount.yaml
    secrets.yaml            # Optional, only for non-managed secret sources
    externalsecrets.yaml    # Default path for External Secrets Operator
```

**Values contract**
- `api.image`, `web.image`, `worker.image`
- `api.env`, `web.env`, `worker.env`
- `api.secrets`, `web.secrets`, `worker.secrets` (env var → secret value; static only)
- `externalSecrets.*.data` (env var → provider secret key; default)
- `ingress.hosts`, `ingress.tls`, `ingress.className`, `ingressPaths.*`
- `resources` + `autoscaling` per workload

### VPS / Single-Server (Compose) Layout (proposed)

Location: `ops/compose/docker-compose.prod.yml`

```
ops/compose/
  docker-compose.prod.yml
  caddy/
    Caddyfile
```

**Design notes**
- Caddy handles TLS + reverse proxy for `/` (web) and `/api` (API) by default.
- Compose uses explicit restart policies, healthchecks, and named volumes for data.
- Production guidance requires `AUTH_KEY_STORAGE_BACKEND=secret-manager`; for VPS defaults, document a minimal Infisical/Vault integration or allow `file` only in demo environments.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Contract Alignment + Docs

| ID | Area | Description | Status |
|----|------|-------------|-------|
| A0 | Design | Lock decisions for GCP compute, secrets, and K8s secret strategy. | ✅ |
| A1 | Design | Finalize shared contract (inputs/outputs) and publish in `docs/ops/hosting-overview.md`. | ✅ |
| A2 | Docs | Add `docs/ops/hosting-gcp.md`, `docs/ops/hosting-kubernetes.md`, `docs/ops/hosting-vps.md`. | ✅ |
| A3 | Docs | Add provider-specific env mapping tables and ops checklists. | ✅ |
| A4 | Docs | Update `docs/ops/setup-wizard-presets.md` to describe GCP infra expectations. | ✅ |
| A5 | Infra/Docs | Refactor AWS/Azure variable names to match the canonical contract and update hosting docs. | ✅ |

### Workstream B – GCP Terraform Blueprint

| ID | Area | Description | Status |
|----|------|-------------|-------|
| B1 | Infra | Scaffold `ops/infra/gcp` with file layout and providers. | ✅ |
| B2 | Infra | Implement VPC + Serverless VPC Access connector. | ✅ |
| B3 | Infra | Implement Cloud SQL Postgres (private IP) + user + DB. | ✅ |
| B4 | Infra | Implement Memorystore Redis (private endpoint). | ✅ |
| B5 | Infra | Implement GCS bucket and IAM for API service account. | ✅ |
| B6 | Infra | Implement Cloud Run services (api/web/worker) + autoscaling settings. | ✅ |
| B7 | Infra | Wire Secret Manager references for `DATABASE_URL` and `REDIS_URL`. | ✅ |
| B8 | Infra | Implement IAM roles + service accounts for GCS, Secret Manager, and Cloud SQL. | ✅ |
| B9 | Infra | Add outputs to align with AWS/Azure (`api_url`, `web_url`, `storage_bucket`, etc.). | ✅ |

### Workstream C – Kubernetes Deployment

| ID | Area | Description | Status |
|----|------|-------------|-------|
| C1 | Infra | Scaffold Helm chart with base templates and helper functions. | ✅ |
| C2 | Infra | Add API/web/worker deployments + services + probes. | ✅ |
| C3 | Infra | Add ingress template with TLS support and class selection. | ✅ |
| C4 | Infra | Add HPA template and resource defaults. | ✅ |
| C5 | Infra | Add External Secrets templates (default) and optional static secrets. | ✅ |
| C6 | Docs | Add Kubernetes runbook + values reference. | ✅ |

### Workstream D – VPS / Single-Server Deployment

| ID | Area | Description | Status |
|----|------|-------------|-------|
| D1 | Infra | Add `docker-compose.prod.yml` with API/web/worker + proxy + optional Postgres/Redis. | ✅ |
| D2 | Infra | Add Caddyfile with HTTPS + routing for `/` and `/api`. | ✅ |
| D3 | Infra | Define volume layout + backup guidance for Postgres/Redis/MinIO. | ✅ |
| D4 | Docs | Add VPS runbook with install, upgrade, and rollback steps. | ✅ |

### Workstream E – CI + Validation

| ID | Area | Description | Status |
|----|------|-------------|-------|
| E1 | CI | Extend CI to run terraform fmt/validate for GCP. | ✅ |
| E2 | CI | Add helm lint/template checks for `ops/charts/starter`. | ✅ |
| E3 | CI | Add compose config validation for `docker-compose.prod.yml`. | ✅ |

### Workstream F – GCP Secret Manager Provider

| ID | Area | Description | Status |
|----|------|-------------|-------|
| F1 | Backend | Implement `gcp_sm` secrets provider with Secret Manager client and caching. | ✅ |
| F2 | Console | Add `starter-console secrets onboard --provider gcp_sm` flow + validation. | ✅ |
| F3 | Docs | Update `docs/security/secrets-providers.md` with GCP Secret Manager runbook. | ✅ |
| F4 | Tests | Add backend + console tests for provider wiring and env validation. | ✅ |

### Workstream G – Engineering Review Remediation

| ID | Area | Description | Status |
|----|------|-------------|-------|
| G1 | Backend | Wrap GCP Secret Manager auth/ADC errors to prevent unhandled exceptions in health checks and CLI probes. | ✅ |
| G2 | Backend | Ensure Secret Manager health checks bypass cache when `force_refresh=True` (Azure/GCP). | ✅ |
| G3 | Tests | Add unit coverage for health-check refresh and GCP auth error wrapping. | ✅ |
| G4 | Backend | Wrap GCP Secret Manager client init/auth errors and surface as structured provider/key-storage errors. | ✅ |
| G5 | Tests | Add env-validation unit tests for gcp_sm (backend + console). | ✅ |

### Engineering Review Findings (2026-01-03)

| ID | Area | Description | Status |
|----|------|-------------|-------|
| R1 | Infra (GCP) | `enable_project_services` only enables compute/vpcaccess/servicenetworking; must include Cloud Run/SQL/Secret Manager/Memorystore/Storage/IAM APIs or document manual enablement. | ⏳ (deferred) |
| R2 | Contracts | Update contract snapshots (`docs/contracts/settings.schema.json`, `docs/contracts/provider_literals.json`) to include `gcp_sm` and GCP settings fields. | ✅ |
| R3 | Console | Add GCP Secret Manager env vars (`GCP_SM_*`) to `WIZARD_PROMPTED_ENV_VARS` coverage inventory. | ✅ |
| R4 | Infra (K8s/Compose) | Auto-disable API-side `ENABLE_BILLING_RETRY_WORKER` when a dedicated worker is enabled to prevent duplicate retries. | ✅ |
| R5 | Docs | Remove stray `\\n+` artifact in `docs/ops/hosting-gcp.md`. | ✅ |

### Remediation Plan (chronological)

| ID | Scope | Long-term approach | Status | Sign-off |
|----|-------|-------------------|--------|----------|
| R1 | Infra (GCP) | Promote required GCP APIs into a Terraform variable with safe defaults; expose `enable_project_services` (and optional override list) in wizard/TUI; add a manual API enablement checklist when disabled. | ⏳ (deferred) | deferred |
| R2 | Contracts | Regenerate contract snapshots after adding `gcp_sm` + GCP settings fields; document snapshots as required when enums/settings change. | ✅ | awaiting |
| R3 | Console | Extend wizard coverage inventory to include `GCP_SM_PROJECT_ID`, `GCP_SM_SIGNING_SECRET_NAME`, `GCP_SM_CACHE_TTL_SECONDS` so audits/snapshots stay accurate. | ✅ | awaiting |
| R4 | Infra (K8s/Compose) | Guard against double retries: Helm auto-sets `ENABLE_BILLING_RETRY_WORKER=false` on API when worker enabled unless explicitly overridden; Compose provides a worker override file that disables API retries. | ✅ | awaiting |
| R5 | Docs | Clean the GCP hosting guide formatting artifact. | ✅ | awaiting |

---

<!-- SECTION: Phases -->
## Phases

| Phase | Scope | Exit Criteria | Status |
| ----- | ----- | ------------- | ------ |
| P0 – Alignment | Finalize provider-agnostic contract, GCP compute target, and K8s secret strategy | Contract doc + decisions logged | ✅ |
| P1 – GCP Blueprint | Implement Terraform and hosting guide | `ops/infra/gcp` + `docs/ops/hosting-gcp.md` complete | ✅ |
| P2 – Kubernetes | Implement Helm chart + runbook | Chart passes lint/template; doc published | ✅ |
| P3 – VPS | Add production Compose + proxy + runbook | Compose stack validated; docs published | ✅ |
| P4 – CI/Docs | CI validation + consolidated docs | CI checks green; overview updated | ⏳ |

---

<!-- SECTION: Dependencies -->
## Dependencies

- Registry strategy for GCP (Artifact Registry default; GHCR supported via credentials).
- No external blockers; decisions for compute and secrets posture are locked.

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Scope creep across providers | High | Lock the env contract first; limit to minimal production blueprint. |
| Inconsistent env mapping | Med | Maintain a single mapping table and shared outputs across providers. |
| Kubernetes complexity | Med | Keep chart minimal; document optional add-ons separately. |
| VPS security gaps | Med | Default to TLS via proxy, strict restart policies, and explicit secrets handling. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- `terraform fmt -check -recursive ops/infra`  
- `terraform -chdir=ops/infra/<provider> init -backend=false` + `terraform validate`
- `helm lint` + `helm template` (or `kustomize build`) for Kubernetes artifacts
- `docker compose -f ops/compose/docker-compose.prod.yml config`
- Manual smoke: deploy API + web, hit `/health/ready` and `/api/health/ready`

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- All new infra is opt-in; no breaking changes to existing AWS/Azure users.
- Runbooks must include migration + rollback guidance.
- CI should validate but not auto-apply Terraform.

---

<!-- SECTION: Changelog -->
## Changelog

- 2026-01-02 — Initial milestone drafted from current repo state and coverage gaps.
- 2026-01-02 — Added design doc, shared contract, and detailed task breakdown.
- 2026-01-02 — Locked GCP/K8s decisions, added GCP Secret Manager provider workstream, and started P0.
- 2026-01-02 — Published deployment contract in `docs/ops/hosting-overview.md`.
- 2026-01-02 — Added GCP/Kubernetes/VPS hosting docs and updated GCP preset mapping.
- 2026-01-02 — Refactored AWS/Azure infra inputs to match the canonical contract.
- 2026-01-02 — Shipped GCP Secret Manager provider across backend + console, plus docs/tests.
- 2026-01-02 — Scaffolded `ops/infra/gcp` with initial Terraform layout and provider wiring.
- 2026-01-02 — Added GCP network foundation (VPC, subnet, VPC Access connector, Private Service Access).
- 2026-01-02 — Added Cloud SQL Postgres (private IP) wiring with database/user provisioning.
- 2026-01-02 — Added Memorystore Redis with private networking defaults.
- 2026-01-02 — Completed GCP Terraform blueprint (Cloud Run, GCS, Secret Manager wiring, IAM, outputs).
- 2026-01-02 — Scaffolded Helm chart base for Kubernetes deployment option.
- 2026-01-02 — Added Kubernetes API/web/worker deployments + services with probes.
- 2026-01-02 — Added ingress template with TLS/class support for Kubernetes chart.
- 2026-01-02 — Added HPA + resource defaults and External Secrets/static secrets support for the chart.
- 2026-01-02 — Published Kubernetes runbook + values reference updates.
- 2026-01-02 — Added production docker-compose stack for VPS deployments.
- 2026-01-02 — Added Caddy reverse proxy config for VPS deployments.
- 2026-01-02 — Documented VPS volume layout, backup guidance, and upgrade steps.
- 2026-01-02 — Extended CI Terraform validation to include GCP.
- 2026-01-02 — Added Helm lint/template checks for the Kubernetes chart.
- 2026-01-02 — Added Docker Compose config validation for the VPS stack.
- 2026-01-02 — Documented and resolved engineering review findings for GCP Secret Manager error handling and health-check refresh behavior.
- 2026-01-02 — Wrapped GCP Secret Manager client init/auth errors and added env-validation tests for gcp_sm (backend + console).
