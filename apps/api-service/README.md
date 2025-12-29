# API Service (FastAPI + OpenAI Agents SDK)

Production-ready FastAPI backend for the OpenAI Agents SaaS starter. This service hosts the AI runtime (agents, workflows, tools, guardrails, streaming), plus the SaaS platform surface (auth, tenants, billing, usage, storage, and observability).

## What this service includes
- OpenAI Agents SDK runtime (openai-agents 0.6.x) with declarative agent specs, tools, handoffs, and structured outputs.
- Deterministic workflows over agents (sequential or parallel with reducers).
- Guardrails for inputs/outputs and tool calls, configurable via presets.
- Tool registry covering OpenAI hosted tools, MCP tools, and custom function tools.
- Vector store + file search orchestration and bindings per tenant/agent.
- Code interpreter container management (auto or explicit containers).
- Multi-tenant auth (Ed25519 JWTs, refresh tokens, MFA, signup policies).
- Stripe billing, usage metering, and rate limits.
- Structured logging, metrics, and activity/run event streams.

## Quick start (local)

Recommended path (generates env files and runs audits):

```bash
# From repo root
just python-bootstrap        # install Python 3.11 + Hatch via uv
just dev-install             # editable installs for shared packages
starter-console setup wizard --profile demo
just api                     # starts FastAPI with env files loaded
```

Manual path:

```bash
cp apps/api-service/.env.local.example apps/api-service/.env.local
just dev-up                  # docker compose: Postgres + Redis (+ optional OTel collector)
just migrate                 # Alembic upgrade heads
just api
```

Once running:
- OpenAPI docs: `http://localhost:8000/docs`
- Health: `GET /health/ready`

## Architecture at a glance

```
apps/api-service/src/app/
├── agents/          # Agent specs + prompts
├── workflows/       # Workflow specs
├── api/             # FastAPI routers + schemas + dependencies
├── services/        # Application services / orchestration
├── infrastructure/  # Providers, persistence, external adapters
├── guardrails/      # Guardrail configs + checks
├── observability/   # Logging + metrics
├── core/            # Settings, security, shared utilities
└── domain/          # Domain models + repository ports
```

Layering rules:
- **API** → **services** → **infrastructure** (no API → infra shortcuts).
- **agents/workflows** are declarative specs; runtime wiring lives under **services** and **infrastructure**.
- Shared contracts live in `packages/starter_contracts`; provider SDK clients live in `packages/starter_providers`.

## AI runtime: agents, tools, guardrails, streaming

### Agents
- Agent specs live in `app/agents/<key>/spec.py` with prompts in `prompt.md.j2`.
- Specs are loaded at startup by the agent registry (see `app/agents/_shared/*`).
- Each agent explicitly declares `tool_keys`; there are no implicit tools.
- Handoffs are controlled via `handoff_keys` + per-target `handoff_context` / overrides.
- Structured outputs use `OutputSpec` with Pydantic schemas or custom validators.
- Model selection resolves `model` → `model_key` → `AGENT_MODEL_DEFAULT` (default `gpt-5.1`).

References:
- `apps/api-service/src/app/agents/README.md`
- `apps/api-service/src/app/agents/CREATING_AGENTS.md`

### Bundled agents
- `triage` (default entrypoint)
- `code_assistant`
- `researcher`
- `retriever`
- `company_intel`
- `compliance_reviewer`
- `director`
- `image_studio`
- `pdf_designer`

### Tools
- Registry: `app/utils/tools/registry.py`.
- Hosted OpenAI tools: `web_search`, `file_search`, `code_interpreter`, `image_generation` (require `OPENAI_API_KEY`).
- Built-ins: `get_current_time`, `search_conversations` (registered by the agent registry).
- MCP tools: configured via `MCP_TOOLS` settings; approval policies enforce allow/deny lists.

### Guardrails
- Guardrails are configured per agent or tool using presets or explicit configs.
- Runtime options (`guardrails_runtime`) control streaming vs blocking behavior and tripwire handling.
- Source of truth: `app/guardrails/README.md` and `docs/integrations/openai-agents-sdk/guardrails/`.

### Streaming
- Raw SDK events are normalized into `AgentStreamEvent` and projected into the public SSE contract.
- Public SSE schema: `docs/contracts/public-sse-streaming/v1.md`.
- Projector: `app/api/v1/shared/public_stream_projector/*`.

## Workflows (deterministic chains over agents)
- Workflow specs live in `app/workflows/<key>/spec.py`.
- Stages can be `sequential` or `parallel`; reducers merge parallel outputs.
- Workflow steps always call existing agents; prompts/tools/guardrails live in the agent spec.

References:
- `apps/api-service/src/app/workflows/README.md`
- `apps/api-service/src/app/workflows/CREATING_WORKFLOWS.md`

### Bundled workflows
- `analysis_code` (sequential)
- `analysis_parallel` (parallel fan-out + reducer)
- `research_report_pdf` (research → PDF synthesis)

## Containers (code interpreter)
- API routes: `app/api/v1/containers`.
- Service: `app/services/containers/service.py`.
- Code interpreter tool can run in **auto** mode (OpenAI-managed) or **explicit** mode (tenant-bound containers).
- Defaults and guardrails live in `app/core/settings/ai.py` (memory tiers, limits, fallback behavior).

Runbook: `docs/runbooks/agents/containers-and-code-interpreter.md`.

## Vector stores & file search
- Vector store service: `app/services/vector_stores/*`.
- API routes: `app/api/v1/vector_stores`.
- Agents opt in via `vector_store_binding` and `file_search_options`.
- Resolution order: request override → agent binding → spec defaults (see `services/vector_stores/README.md`).

Runbook: `docs/runbooks/agents/vector-stores-and-file-search.md`.

## Storage & assets
- Storage service: `app/services/storage/service.py` (S3, GCS, MinIO, Azure Blob via `starter_providers`).
- Asset service: `app/services/assets/service.py` manages uploaded/generated assets.
- API routes: `app/api/v1/storage`, `app/api/v1/uploads`, `app/api/v1/assets`.

## SaaS platform features

### Authentication & tenants
- Access tokens are EdDSA/Ed25519 JWTs; JWKS served from `/.well-known/jwks.json`.
- Refresh tokens are hashed and stored in Postgres with a Redis cache for fast lookup.
- MFA is supported for login flows.
- Signup policies: `public`, `invite_only`, or `approval` (see `signup_access_policy`).
- Tenant context enforced via JWT claims and API dependencies (`X-Tenant-Id` is validated against token claims).

Key files:
- `app/core/security.py` (JWT signing/verification)
- `app/services/auth/*`, `app/services/users/*`, `app/api/v1/auth/*`
- `docs/security/auth-review-brief.md`

### Service accounts
- Service account tokens are issued via the auth service and audited.
- Browser-initiated issuance uses Vault/secret-provider signing (`ServiceAccountIssuanceBridge`).
- Console helpers live under `starter-console auth ...`.

### Billing & usage
- Stripe integration: plans, webhooks, event replay, retry worker.
- Usage metering and entitlement enforcement with plan-aware limits.
- API routes: `app/api/v1/billing`, `app/api/v1/usage`.

Runbooks:
- `docs/billing/stripe-setup.md`
- `docs/ops/db-release-playbook.md`
- `docs/ops/usage-guardrails-runbook.md`

## Observability
- Structured JSON logging with configurable sinks (`stdout`, `file`, `otlp`, `datadog`).
- Log context automatically binds correlation/tenant/user IDs.
- Metrics exposed for Prometheus.

References:
- `docs/observability/README.md`
- `docs/architecture/structured-logging.md`

## Developer workflows

### Migrations
Use Just recipes (they wire env loading and handle multi-heads):

```bash
just migrate
just migration-revision message="add widget table"
```

### Tests
```bash
cd apps/api-service
hatch run lint
hatch run typecheck
hatch run test
```

Targeted suites:
```bash
cd apps/api-service
hatch run test-unit
hatch run test-integration
hatch run test-smoke
```

### OpenAPI export
Use the console so the schema matches billing + fixtures. Preferred:

```bash
just openapi-export
```

Manual (if you need to run the commands directly):

```bash
cd packages/starter_console
starter-console api export-openapi \
  --output apps/api-service/.artifacts/openapi.json \
  --enable-billing
starter-console api export-openapi \
  --output apps/api-service/.artifacts/openapi-fixtures.json \
  --enable-billing \
  --enable-test-fixtures
```

## Deployment
- Dockerfile: `apps/api-service/Dockerfile`.
- Production runbooks: `docs/ops/runbook-release.md`, `docs/ops/container-deployments.md`.
- Migrations must be run as a one-off job (`just migrate` or `starter-console release db`).

---

If you’re extending the AI runtime, start with the agent and workflow guides above; if you’re changing SaaS platform behavior, use the runbooks to keep auth/billing/usage consistent across environments.
