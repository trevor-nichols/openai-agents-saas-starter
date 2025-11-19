set shell := ["bash", "-uc"]

# Select the application env file: prefer .env.local, fall back to .env
env_file := `python -c "import os; print(next((f for f in ['.env.local', '.env'] if os.path.exists(f)), ''))"`

# Environment runner wrapper
env_runner := "python scripts/run_with_env.py"
vault_dev_compose := "docker compose -f docker-compose.vault-dev.yml"

# Defaults
vault_dev_port := "18200"
vault_dev_root_token_id := "vault-dev-root"
vault_dev_host_addr := "http://127.0.0.1:" + vault_dev_port
vault_transit_key := "auth-service"

setup_user_email := "dev@example.com"
setup_user_name := "Dev Admin"
setup_user_password := ""
setup_user_tenant := "default"
setup_user_tenant_name := "Default Tenant"
setup_user_role := "admin"
setup_service_account := "demo-bot"
setup_service_scopes := "chat:write,conversations:read"
setup_service_tenant := ""
setup_staging_answers := ""
setup_production_answers := ""

# Computed variables
staging_answer_flags := if setup_staging_answers != "" { "--non-interactive --answers-file " + setup_staging_answers } else { "" }
service_tenant_flag := if setup_service_tenant != "" { "--tenant " + setup_service_tenant } else { "" }

# Helper to ensure env file exists
_check_env:
    @if [ -z "{{env_file}}" ]; then \
        echo "Error: No .env.local or .env file found. Create one before running tasks."; \
        exit 1; \
    fi

# List available commands
default:
    @just --list

help:
    @echo "Available commands:" && \
    echo "  just dev-up                 # Start Postgres + Redis using .env.compose and {{env_file}}" && \
    echo "  just dev-down               # Stop the infrastructure stack" && \
    echo "  just dev-logs               # Tail Postgres/Redis logs" && \
    echo "  just dev-ps                 # Show running containers" && \
    echo "  just vault-up               # Start the local Vault dev signer" && \
    echo "  just vault-down             # Stop the local Vault dev signer" && \
    echo "  just vault-logs             # Tail logs for the dev Vault container" && \
    echo "  just verify-vault           # Spin up Vault dev + run CLI issuance smoke test" && \
    echo "  just migrate                # Run Alembic migrations with current env" && \
    echo "  just migration-revision     # Create a new Alembic revision" && \
    echo "  just bootstrap              # Provision the Hatch environment" && \
    echo "  just api                    # Run the FastAPI server via hatch" && \
    echo "  just test-stripe            # Run fixture-driven Stripe replay tests" && \
    echo "  just stripe-replay args     # Invoke the Stripe replay CLI" && \
    echo "  just lint-stripe-fixtures   # Validate Stripe fixture JSON files" && \
    echo "  just cli cmd                # Run the consolidated operator CLI" && \
    echo "  just setup-local-lite       # Run Starter CLI wizard with Local-Lite defaults" && \
    echo "  just setup-local-full       # Run Starter CLI wizard with Local-Full automation" && \
    echo "  just setup-staging          # Run Starter CLI wizard with staging-safe automation" && \
    echo "  just setup-production       # Headless production-ready wizard run" && \
    echo "  just seed-dev-user          # Ensure Compose is up and seed a developer account" && \
    echo "  just issue-demo-token       # Issue a service-account refresh token"

# Provision the Hatch environment with project dependencies
bootstrap:
    @echo "Creating/refreshing the Hatch environment"
    hatch env create

# Start FastAPI via hatch run serve
api: _check_env
    @echo "Starting FastAPI via hatch run serve"
    {{env_runner}} .env.compose {{env_file}} -- hatch run serve

# Run Alembic migrations with current env
migrate: _check_env
    @echo "Using .env.compose + {{env_file}}"
    {{env_runner}} .env.compose {{env_file}} -- hatch run migrate

# Create a new Alembic revision (usage: just migration-revision "message")
migration-revision message: _check_env
    @echo "Using .env.compose + {{env_file}}"
    {{env_runner}} .env.compose {{env_file}} -- hatch run migration-revision "{{message}}"

# Start Postgres + Redis using .env.compose and env file
dev-up: _check_env
    {{env_runner}} .env.compose {{env_file}} -- python ops/observability/render_collector_config.py
    {{env_runner}} .env.compose {{env_file}} -- bash -c '\
        set -euo pipefail; \
        services="postgres redis"; \
        collector_msg=""; \
        if [ "${ENABLE_OTEL_COLLECTOR:-false}" = "true" ]; then \
            services="${services} otel-collector"; \
            collector_msg=" + otel-collector (ports ${OTEL_COLLECTOR_HTTP_PORT:-4318}/${OTEL_COLLECTOR_GRPC_PORT:-4317})"; \
        fi; \
        echo "Starting ${services}${collector_msg}"; \
        docker compose up -d ${services}; \
    '

# Stop the infrastructure stack
dev-down: _check_env
    {{env_runner}} .env.compose {{env_file}} -- docker compose down

# Tail Postgres/Redis logs
dev-logs: _check_env
    {{env_runner}} .env.compose {{env_file}} -- bash -c '\
        services="postgres redis"; \
        if [ "${ENABLE_OTEL_COLLECTOR:-false}" = "true" ]; then \
            services="${services} otel-collector"; \
        fi; \
        docker compose logs -f --tail=100 ${services}; \
    '

# Show running containers
dev-ps: _check_env
    {{env_runner}} .env.compose {{env_file}} -- docker compose ps

# Start the local Vault dev signer
vault-up:
    @echo "Starting Vault dev signer on {{vault_dev_host_addr}}"
    VAULT_DEV_PORT={{vault_dev_port}} VAULT_DEV_ROOT_TOKEN_ID={{vault_dev_root_token_id}} {{vault_dev_compose}} up -d
    VAULT_ADDR={{vault_dev_host_addr}} scripts/vault/wait-for-dev.sh
    HOST_VAULT_ADDR={{vault_dev_host_addr}} VAULT_DEV_ROOT_TOKEN_ID={{vault_dev_root_token_id}} VAULT_TRANSIT_KEY={{vault_transit_key}} {{vault_dev_compose}} exec vault-dev /vault/dev-init.sh

# Stop the local Vault dev signer
vault-down:
    {{vault_dev_compose}} down

# Tail logs for the dev Vault container
vault-logs:
    {{vault_dev_compose}} logs -f --tail=200

# Spin up Vault dev + run CLI issuance smoke test
verify-vault: vault-up _check_env
    @echo "Running service-account issuance via starter CLI (ensure FastAPI is reachable)."
    VAULT_ADDR={{vault_dev_host_addr}} \
    VAULT_TOKEN={{vault_dev_root_token_id}} \
    VAULT_TRANSIT_KEY={{vault_transit_key}} \
    VAULT_VERIFY_ENABLED=true \
    {{env_runner}} .env.compose {{env_file}} -- python -m starter_cli.app auth tokens issue-service-account --account dev-automation --scopes conversations:read --output text

# Run fixture-driven Stripe replay tests
test-stripe: _check_env
    {{env_runner}} .env.compose {{env_file}} -- hatch run pytest -m stripe_replay

# Invoke the Stripe replay CLI (usage: just stripe-replay "list --status failed")
stripe-replay args: _check_env
    {{env_runner}} .env.compose {{env_file}} -- python scripts/stripe/replay_events.py {{args}}

# Validate Stripe fixture JSON files
lint-stripe-fixtures:
    python scripts/stripe/replay_events.py validate-fixtures

# Check docs/trackers/CLI_ENV_INVENTORY.md vs runtime settings
cli-verify-env:
    python -m scripts.cli.verify_env_inventory

# Validate Stripe/Resend/Tavily env configuration
validate-providers:
    python -m starter_cli.app providers validate

# Run the consolidated operator CLI (usage: just cli "providers validate")
cli cmd:
    python -m starter_cli.app {{cmd}}

# Run Starter CLI wizard with Local-Lite defaults + seed a dev user
setup-local-lite:
    python -m starter_cli.app infra deps
    python -m starter_cli.app setup wizard \
        --profile local \
        --auto-infra \
        --auto-secrets \
        --auto-migrations \
        --auto-redis \
        --no-auto-geoip
    just seed-dev-user \
        setup_user_email="{{setup_user_email}}" \
        setup_user_name="{{setup_user_name}}" \
        setup_user_password="{{setup_user_password}}" \
        setup_user_tenant="{{setup_user_tenant}}" \
        setup_user_tenant_name="{{setup_user_tenant_name}}" \
        setup_user_role="{{setup_user_role}}"
    @echo ""
    @echo "Next steps:"
    @echo "  1. Run 'just api' in a new terminal to start FastAPI."
    @echo "  2. Once the API is up, run 'just issue-demo-token' to mint a service-account token."

# Run Starter CLI wizard with Local-Full automation toggles
setup-local-full:
    python -m starter_cli.app infra deps
    python -m starter_cli.app setup wizard \
        --profile local \
        --auto-infra \
        --auto-secrets \
        --auto-migrations \
        --auto-redis \
        --auto-geoip \
        --auto-stripe
    just seed-dev-user \
        setup_user_email="{{setup_user_email}}" \
        setup_user_name="{{setup_user_name}}" \
        setup_user_password="{{setup_user_password}}" \
        setup_user_tenant="{{setup_user_tenant}}" \
        setup_user_tenant_name="{{setup_user_tenant_name}}" \
        setup_user_role="{{setup_user_role}}"
    @echo ""
    @echo "Local-Full ready. Start FastAPI with 'just api' and run 'just issue-demo-token' if needed."

# Run Starter CLI wizard with staging-safe automation
setup-staging:
    python -m starter_cli.app infra deps
    python -m starter_cli.app setup wizard \
        --profile staging \
        --no-auto-infra \
        --no-auto-secrets \
        --auto-migrations \
        --auto-redis \
        --auto-geoip \
        {{staging_answer_flags}}

# Headless production-ready wizard run
setup-production:
    @if [ -z "{{setup_production_answers}}" ]; then \
        echo "Error: set setup_production_answers=/absolute/path/to/answers.json"; \
        exit 1; \
    fi
    python -m starter_cli.app infra deps
    python -m starter_cli.app setup wizard \
        --profile production \
        --strict \
        --answers-file {{setup_production_answers}} \
        --no-auto-infra \
        --no-auto-secrets \
        --auto-migrations \
        --auto-redis \
        --auto-geoip

# Ensure Compose is up and seed a developer account
seed-dev-user: dev-up _check_env
    {{env_runner}} .env.compose {{env_file}} -- bash -c ' \
        set -euo pipefail; \
        cmd=(python scripts/seed_users.py \
            --email "{{setup_user_email}}" \
            --tenant-slug "{{setup_user_tenant}}" \
            --tenant-name "{{setup_user_tenant_name}}" \
            --role "{{setup_user_role}}" \
            --display-name "{{setup_user_name}}"); \
        if [ -n "{{setup_user_password}}" ]; then \
            cmd+=(--password "{{setup_user_password}}"); \
        fi; \
        echo "Seeding user with email {{setup_user_email}}"; \
        "${cmd[@]}"; \
    '

# Issue a service-account refresh token (requires API running)
issue-demo-token:
    @echo "Ensure FastAPI is running (e.g., 'just api') before issuing a token."
    python -m starter_cli.app auth tokens issue-service-account \
        --account "{{setup_service_account}}" \
        --scopes "{{setup_service_scopes}}" \
        {{service_tenant_flag}} \
        --output json
