# Acme - Extensible AI Agent System

A FastAPI-based AI agent system built with the OpenAI Agents SDK, designed for easy extension from single agent to multiagent systems.

## 🚀 Features

- **Extensible Triage Pattern**: Start with a single main agent, easily add specialized agents
- **Conversation Management**: Persistent conversation history with context awareness
- **Streaming Support**: Real-time streaming responses for better UX
- **Multiple Agent Types**: Ready-to-activate specialized agents (code, data analysis, etc.)
- **RESTful API**: Clean, documented API endpoints
- **Type Safety**: Full Pydantic validation and type hints

## 🏗️ Architecture

### Current Implementation: Single Agent with Extension Points

```
User → Triage Agent (Main Chatbot)
         ↓
    [Future: Specialized Agents]
```

### Future Multiagent Capabilities

```
User → Triage Agent → Code Assistant
                   → Data Analyst  
                   → Research Agent
                   → Custom Agents
```

## 📁 Project Structure

```
api-service/
├── app/
│   ├── api/
│   │   ├── models/     # Public request/response schemas
│   │   ├── dependencies/ # Shared FastAPI dependencies
│   │   ├── errors.py   # Global exception handlers
│   │   └── v1/         # Versioned REST surface (`/api/v1/...`)
│   ├── core/           # Configuration and security
│   ├── domain/         # Domain objects and repository contracts
│   ├── infrastructure/ # External adapters (OpenAI runner, persistence)
│   ├── services/       # Business logic (Agent orchestration)
│   ├── middleware/     # Custom middleware
│   └── utils/          # Utility functions
├── tests/              # Test suite
└── main.py            # FastAPI application
```

## 🛠️ Setup

### 1. Install Tooling

We use [Hatch](https://hatch.pypa.io/) to manage virtual environments and scripts.

```bash
pipx install hatch  # or: pip install --user hatch
```

### 2. Create the Development Environment

```bash
hatch env create
```

This provisions a local virtualenv with all runtime and developer dependencies defined in `pyproject.toml`.

### 3. Environment Configuration

Copy `.env.local.example` to `.env.local` and configure every secret (do **not** reuse the sample values outside local dev). Sections are labeled to indicate what is **required** vs **optional** in production; the CLI setup wizard will surface the same groupings. Highlights:

```bash
# Core application (required)
ENVIRONMENT=development
DEBUG=true
PORT=8000
APP_PUBLIC_URL=http://localhost:3000
ALLOWED_HOSTS=localhost,localhost:8000,127.0.0.1,testserver,testclient
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# Secrets (replace before production)
SECRET_KEY=change-me
AUTH_PASSWORD_PEPPER=change-me-too
AUTH_REFRESH_TOKEN_PEPPER=change-me-again
AUTH_EMAIL_VERIFICATION_TOKEN_PEPPER=change-me-email
AUTH_PASSWORD_RESET_TOKEN_PEPPER=change-me-reset
AUTH_SESSION_ENCRYPTION_KEY=   # required for encrypted session metadata in prod
AUTH_SESSION_IP_HASH_SALT=

# Persistence / Redis
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/anything_agents
REDIS_URL=redis://localhost:6379/0
BILLING_EVENTS_REDIS_URL=
AUTO_RUN_MIGRATIONS=false      # dev convenience only

# Rate limits & auth policies (tune per env)
REQUIRE_EMAIL_VERIFICATION=true
CHAT_RATE_LIMIT_PER_MINUTE=60
CHAT_STREAM_RATE_LIMIT_PER_MINUTE=30
CHAT_STREAM_CONCURRENT_LIMIT=5
BILLING_STREAM_RATE_LIMIT_PER_MINUTE=20
BILLING_STREAM_CONCURRENT_LIMIT=3
PASSWORD_RESET_TOKEN_TTL_MINUTES=30
PASSWORD_RESET_EMAIL_RATE_LIMIT_PER_HOUR=5
PASSWORD_RESET_IP_RATE_LIMIT_PER_HOUR=20
EMAIL_VERIFICATION_TOKEN_TTL_MINUTES=60
EMAIL_VERIFICATION_EMAIL_RATE_LIMIT_PER_HOUR=3
EMAIL_VERIFICATION_IP_RATE_LIMIT_PER_HOUR=10
AUTH_PASSWORD_HISTORY_COUNT=5
AUTH_LOCKOUT_THRESHOLD=5
AUTH_LOCKOUT_WINDOW_MINUTES=60
AUTH_LOCKOUT_DURATION_MINUTES=60
AUTH_IP_LOCKOUT_THRESHOLD=50
AUTH_IP_LOCKOUT_WINDOW_MINUTES=10
AUTH_IP_LOCKOUT_DURATION_MINUTES=10
AUTH_JWKS_CACHE_SECONDS=300
AUTH_JWKS_MAX_AGE_SECONDS=300
AUTH_JWKS_ETAG_SALT=local-jwks-salt

# Billing (set when ENABLE_BILLING=true)
ENABLE_BILLING=false
ENABLE_BILLING_STREAM=false
ENABLE_BILLING_RETRY_WORKER=true
ENABLE_BILLING_STREAM_REPLAY=true
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_PRODUCT_PRICE_MAP={"starter":"price_xxx"}

# Providers
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GEMINI_API_KEY=
XAI_API_KEY=
TAVILY_API_KEY=

# Email Delivery (Resend)
RESEND_EMAIL_ENABLED=false
RESEND_API_KEY=
RESEND_DEFAULT_FROM=support@example.com
RESEND_BASE_URL=https://api.resend.com
RESEND_EMAIL_VERIFICATION_TEMPLATE_ID=
RESEND_PASSWORD_RESET_TEMPLATE_ID=

# Vault Transit (Starter CLI sets true for staging/production)
VAULT_VERIFY_ENABLED=false
VAULT_ADDR=
VAULT_TOKEN=
VAULT_TRANSIT_KEY=auth-service
```

Flip `RESEND_EMAIL_ENABLED=true` only after you have verified the sender domain inside Resend and populated both `RESEND_API_KEY` and `RESEND_DEFAULT_FROM`. Leave the template ID and Vault fields empty for local development—the backend uses safe defaults until you enable those features—but treat every pepper/secret as mandatory before staging or production. As of November 2025 the API refuses to boot with `ENVIRONMENT` other than `development/dev/local/test` (or with `DEBUG=false`) unless `VAULT_VERIFY_ENABLED=true` **and** the Vault fields are populated. The Starter CLI wizard enforces this automatically for `--profile staging|production` runs, prompting for Vault Transit connectivity and writing the necessary env vars.

### Unified CLI (backend + frontend tooling)

Prefer not to edit env files manually? Run the consolidated operator CLI:

```bash
python -m starter_cli.app setup wizard        # full interactive flow
just cli cmd="setup wizard --profile=production"  # helper wrapper
python -m starter_cli.app infra deps          # check Docker/Hatch/Node/pnpm availability
python -m starter_cli.app infra compose up    # start Postgres + Redis via docker compose
python -m starter_cli.app infra vault up      # run the Vault dev signer helper
```

The wizard now walks through profiles (local/staging/production), captures required vs. optional secrets, verifies Vault Transit connectivity before enabling service-account issuance, validates Stripe/Redis/Resend inputs (with optional migration + seeding helpers), and records tenant/logging/GeoIP/signup policies so auditors can trace every decision. It writes `.env.local` + `web-app/.env.local`, then emits a milestone-aligned report. Stripe provisioning and auth tooling now live exclusively under the consolidated CLI (`python -m starter_cli.app stripe …`, `python -m starter_cli.app auth …`).

After the wizard, use the new `infra` command group instead of raw Just recipes:

- `python -m starter_cli.app infra compose up|down|logs|ps` – wraps `just dev-*` helpers for Docker Compose.
- `python -m starter_cli.app infra vault up|down|logs|verify` – manages the Vault dev signer lifecycle.
- `python -m starter_cli.app config dump-schema --format table` – lists every backend env var, its default, and whether the wizard collected it. The full inventory also lives in `docs/trackers/CLI_ENV_INVENTORY.md`.
- `just cli-verify-env` – runs the inventory verification script to ensure the markdown table stays in sync with the runtime schema (useful in CI or before merging infra changes).
- Every wizard run writes a JSON audit report (default `var/reports/setup-summary.json`; override via `--summary-path`) so you can archive the collected inputs alongside deployment artifacts.

### 4. Run the Application

```bash
hatch run serve
```

The API will be available at `http://localhost:8000`

> **Compose vs. application env files**
> - `.env.compose` (tracked) holds the non-sensitive defaults that Docker Compose needs (ports, default credentials, project name). You should not edit this file.
> - `.env.local` (gitignored) contains your secrets and any overrides. The Make targets below source **both** files, so you never have to `export` variables manually.
> - `.env.compose` now sets `DATABASE_URL`, so durable Postgres storage is the out-of-the-box behavior.

### 5. Database & Migrations

1. Start the infrastructure stack (Postgres + Redis) via the helper, which automatically sources `.env.compose` and your `.env.local`:
   ```bash
   just dev-up
   ```
   *(Stop later with `just dev-down`. Data persists inside the `postgres-data` / `redis-data` volumes.)*
2. Apply the baseline migration:
   ```bash
   just migrate
   ```
3. Generate new migrations as the schema evolves:
   ```bash
   just migration-revision message="add widget table"
   ```

### 6. Seed a Local Admin User

Once Postgres is running and the new auth tables are migrated, create a bootstrap user via the CLI (the Just recipes automatically load both `.env.compose` and `.env.local`):

```bash
python -m starter_cli.app users seed --email admin@example.com --tenant-slug default --role admin
```

You will be prompted for the password unless you pass `--password`. The command ensures the tenant exists, hashes the password with the configured pepper, stores password history, and prints the resulting credentials for quick testing.

### 7. Quality Checks

Run the standard backend quality gates before opening a PR:

```bash
python scripts/check_secrets.py
hatch run lint
hatch run typecheck
hatch run pyright
hatch run test
```

### 8. Postgres Integration Smoke Tests

Provision a Postgres instance (see step 5), then run:

```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/anything_agents \
hatch run pytest api-service/tests/integration -m postgres
```

The test suite creates a throwaway database, applies Alembic migrations, and verifies the Postgres conversation and billing repositories.

> **Note:** Billing endpoints require Postgres. Configure `DATABASE_URL`, then flip `ENABLE_BILLING=true`; the app fails fast if durable storage or Stripe secrets are missing.

### 9. Billing API (Postgres Only)

Billing routes derive tenant identity/role from the JWT payload. Optional headers are still accepted for backwards compatibility, but they must **match or down-scope** the token claims:

- `X-Tenant-Id` (optional): must match the `tenant_id` embedded in the access token if supplied.
- `X-Tenant-Role` (optional): may request a lower role (`owner` > `admin` > `viewer`) but cannot elevate beyond what the token grants.

Example: start a subscription (requires role `owner` or `admin`):

```bash
curl -X POST "http://localhost:8000/api/v1/billing/tenants/tenant-123/subscription" \
     -H "Authorization: Bearer <token>" \
     -H "X-Tenant-Id: tenant-123" \
     -H "X-Tenant-Role: owner" \
     -H "Content-Type: application/json" \
     -d '{"plan_code": "starter", "billing_email": "owner@example.com", "auto_renew": true}'
```

Report usage (idempotent when `idempotency_key` repeated):

```bash
curl -X POST "http://localhost:8000/api/v1/billing/tenants/tenant-123/usage" \
     -H "Authorization: Bearer <token>" \
     -H "X-Tenant-Id: tenant-123" \
     -H "X-Tenant-Role: admin" \
     -H "Content-Type: application/json" \
     -d '{"feature_key": "messages", "quantity": 120, "idempotency_key": "messages-2025-11-06"}'
```

#### Stripe configuration

Billing routes now require Stripe credentials whenever `ENABLE_BILLING=true`. The quickest path is to run the consolidated operator CLI via `python -m starter_cli.app stripe setup` (aliased by `pnpm stripe:setup`), which prompts for your Stripe secret/webhook secrets, asks how much to charge for the Starter + Pro plans, and then creates/reuses the corresponding Stripe products/prices (7-day trial included). The CLI writes `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, and `STRIPE_PRODUCT_PRICE_MAP` into `.env.local` and flips `ENABLE_BILLING=true` for you. Prefer manual edits? You can still populate those keys yourself—just keep the JSON map in sync with your real Stripe price IDs. See `docs/billing/stripe-setup.md` for the full checklist.

## 📈 Observability & Logging

- FastAPI + worker entrypoints call `app.observability.logging.configure_logging(get_settings())`, which wires the JSON formatter and sink declared via `LOGGING_SINK` (`stdout`, `datadog`, `otlp`, or `none`). When the Starter CLI flips `ENABLE_OTEL_COLLECTOR=true`, `LOGGING_OTLP_ENDPOINT` defaults to `http://otel-collector:4318/v1/logs`, so the app streams logs into the bundled OpenTelemetry Collector automatically. Set `LOGGING_DATADOG_API_KEY`/`LOGGING_DATADOG_SITE` or `LOGGING_OTLP_ENDPOINT` (+ optional `LOGGING_OTLP_HEADERS` JSON) before switching sinks; startup fails fast when configuration is incomplete.
- Request middleware seeds a scoped `log_context`, so every `log_event(...)` down-stack inherits `correlation_id`, `tenant_id`, and `user_id` automatically. Background workers bind their own `worker_id`, ensuring Stripe replay jobs, Resend adapters, etc., land in the same pipeline. See `docs/architecture/structured-logging.md` for the canonical schema.
- The bundled collector + exporter workflow is documented in `docs/observability/README.md`, including the env vars that control the collector container (`ENABLE_OTEL_COLLECTOR`, `OTEL_EXPORTER_SENTRY_*`, `OTEL_EXPORTER_DATADOG_*`, etc.) and how to forward logs to Sentry/Datadog in a few clicks.
- Sample stdout entry:

```json
{
  "ts": "2025-11-17T09:00:00.123Z",
  "event": "http.response",
  "level": "info",
  "correlation_id": "3c6c72f0-3af7-4a40-b655-a1859d4373af",
  "tenant_id": "tenant-42",
  "user_id": "5f1a",
  "status_code": 200,
  "duration_ms": 42.1,
  "fields": {
    "status_code": 200,
    "duration_ms": 42.1
  }
}
```

Every sink receives the same schema, so Datadog and OTLP collectors ingest identical payloads when enabled.

## 🤖 Agent Types

### Current Agents

1. **Triage Agent** (Active)
   - Main conversational interface
   - Handles general queries
   - Routes to specialized agents (future)
   - Tools: time, conversation search

2. **Code Assistant** (Ready to activate)
   - Code review and debugging
   - Architecture suggestions
   - Best practices guidance

3. **Data Analyst** (Ready to activate)
   - Data interpretation
   - Statistical analysis
   - Visualization suggestions

## 📡 API Endpoints

### Chat with Agents

```bash
# Basic chat
POST /api/v1/chat
{
  "message": "Hello, how can you help me?",
  "agent_type": "triage",
  "conversation_id": "optional-uuid"
}

# Streaming chat
POST /api/v1/chat/stream
# Returns Server-Sent Events stream

> **Rate limits:** Chat and streaming endpoints enforce per-user quotas (`CHAT_RATE_LIMIT_PER_MINUTE`, `CHAT_STREAM_RATE_LIMIT_PER_MINUTE`) plus concurrent stream caps (`CHAT_STREAM_CONCURRENT_LIMIT`). Adjust these environment variables (see `.env.local.example`) to tune throughput per environment and watch for HTTP 429 responses if callers exceed the limits.
```

### Conversation Management

```bash
# List conversations
GET /api/v1/conversations

# Get conversation history
GET /api/v1/conversations/{conversation_id}

# Clear conversation
DELETE /api/v1/conversations/{conversation_id}
```

### Agent Management

```bash
# List available agents
GET /api/v1/agents

# Get agent status
GET /api/v1/agents/{agent_name}/status
```

## 🔧 Extending to Multiagent System

### Option 1: Activate Existing Specialized Agents

Simply modify the triage agent's instructions to include handoffs:

```python
# In app/services/agent_service.py
self._agents["triage"] = Agent(
    name="Triage Assistant",
    instructions="""
    You are the main AI assistant. For coding questions, 
    handoff to the code assistant. For data questions, 
    handoff to the data analyst.
    """,
    handoffs=[
        self._agents["code_assistant"],
        self._agents["data_analyst"]
    ]
)
```

### Option 2: Add New Specialized Agents

```python
# Add to AgentFactory._initialize_agents()
self._agents["research_agent"] = Agent(
    name="Research Specialist",
    instructions="You specialize in research and fact-checking...",
    tools=[web_search_tool, citation_tool]
)
```

### Option 3: Agents as Tools Pattern

```python
# Use agents as tools instead of handoffs
orchestrator = Agent(
    name="Orchestrator",
    tools=[
        code_agent.as_tool("code_help", "Get coding assistance"),
        data_agent.as_tool("data_analysis", "Analyze data")
    ]
)
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run agent-specific tests
pytest tests/test_agents.py

# Run with coverage
pytest --cov=app tests/

# Replay Stripe fixtures through the webhook + SSE stack
just test-stripe

# Validate and replay stored Stripe events (examples)
just lint-stripe-fixtures
just stripe-replay args="list --handler billing_sync --status failed"
just stripe-replay args="replay --dispatch-id 7ad7c7bc-..."
```

## 🔄 Migration Path: Single → Multiagent

### Phase 1: Single Agent (Current)
- ✅ Triage agent handles all requests
- ✅ Conversation management
- ✅ Extensible architecture in place

### Phase 2: Selective Handoffs
- Activate specific specialized agents
- Add handoff logic to triage agent
- Minimal code changes required

### Phase 3: Full Multiagent System
- Multiple active agents
- Complex routing logic
- Agent-to-agent communication

### Phase 4: Advanced Features
- Dynamic agent creation
- Agent learning and adaptation
- Custom tool integration

## 🎯 Example Usage

### Simple Chat

```python
import requests

response = requests.post("http://localhost:8000/api/v1/agents/chat", json={
    "message": "Explain quantum computing in simple terms"
})

print(response.json()["response"])
```

### Conversation with Context

```python
# First message
response1 = requests.post("http://localhost:8000/api/v1/agents/chat", json={
    "message": "I'm working on a Python web app"
})

conversation_id = response1.json()["conversation_id"]

# Follow-up with context
response2 = requests.post("http://localhost:8000/api/v1/agents/chat", json={
    "message": "What framework should I use?",
    "conversation_id": conversation_id
})
```

## 🚀 Deployment

### Docker (Recommended)

```dockerfile
FROM python:3.11-slim
WORKDIR /app

# Install runtime dependencies and the service package
COPY pyproject.toml .
COPY LICENSE .
COPY run.py .
COPY api-service ./api-service
RUN pip install --upgrade pip && pip install --no-cache-dir .

# Provide application defaults (optional)
ENV HOST=0.0.0.0 \
    PORT=8000 \
    RELOAD=false

CMD ["api-service"]
```

### Production Considerations

- Use Redis for conversation storage
- Implement proper authentication
- Add rate limiting
- Monitor agent performance
- Set up logging and tracing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

---

**Ready to build something amazing with AI agents? Start with the single agent and scale to multiagent systems as your needs grow!** 🚀 
Run `python scripts/check_secrets.py` (or add it to CI) to verify you replaced every placeholder secret before deploying. Production/staging boots will now fail fast if `ENVIRONMENT` isn’t a dev value and the defaults remain.
