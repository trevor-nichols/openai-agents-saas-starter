set shell := ["bash", "-uc"]

# Root orchestrator: delegates to per-package Justfiles and shared infra.

# Env + helpers
env_file := `python -c "import os; print(next((f for f in ['.env.local', '.env'] if os.path.exists(f)), ''))"`
repo_root := justfile_directory()
env_runner := "cd packages/starter_cli && hatch run python -m starter_cli.app --skip-env util run-with-env " + repo_root + "/.env.compose " + repo_root + "/" + env_file
api_just := "just -f apps/api-service/justfile"
cli_just := "just -f packages/starter_cli/justfile"
contracts_just := "just -f packages/starter_contracts/justfile"
web_just := "just -f apps/web-app/justfile"
compose_file := "ops/compose/docker-compose.yml"
vault_compose_file := "ops/compose/docker-compose.vault-dev.yml"
minio_compose_file := "ops/compose/docker-compose.minio.yml"
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
staging_answer_flags := if setup_staging_answers != "" { "--non-interactive --answers-file " + setup_staging_answers } else { "" }
service_tenant_flag := if setup_service_tenant != "" { "--tenant " + setup_service_tenant } else { "" }

_check_env:
    @if [ -z "{{env_file}}" ]; then \
        echo "Error: No .env.local or .env file found. Create one before running tasks."; \
        exit 1; \
    fi

default:
    @just --list

help:
    @echo "Core commands:" && \
    echo "  just dev-up                 # Start Postgres/Redis (and otel if enabled)" && \
    echo "  just dev-down               # Stop infra stack" && \
    echo "  just dev-logs               # Tail infra logs" && \
    echo "  just dev-ps                 # Show infra containers" && \
    echo "  just api                    # Start FastAPI (delegates to apps/api-service/justfile)" && \
    echo "  just migrate                # Run Alembic migrations" && \
    echo "  just migration-revision \"msg\" # Create Alembic revision" && \
    echo "  just bootstrap              # Create api-service hatch env" && \
    echo "  just start-dev              # CLI start: compose + backend + frontend" && \
    echo "  just start-backend          # CLI start backend only" && \
    echo "  just start-frontend         # CLI start frontend only" && \
    echo "  just vault-up|vault-down    # Start/stop local Vault dev" && \
    echo "  just stripe-replay args     # Stripe dispatch replay via CLI" && \
    echo "  just stripe-listen          # Capture Stripe webhook secret" && \
    echo "  just lint-stripe-fixtures   # Validate Stripe fixtures" && \
    echo "  just doctor                 # CLI doctor report" && \
    echo "  just seed-dev-user          # Seed a developer account" && \
    echo "  just issue-demo-token       # Issue service-account token" && \
    echo "Package helpers:" && \
    echo "  just backend-lint|typecheck|test    # Delegates to api-service" && \
    echo "  just cli-lint|typecheck|test        # Delegates to packages/starter_cli" && \
    echo "  just contracts-lint|typecheck|test  # Delegates to packages/starter_contracts" && \
    echo "  just web-lint|typecheck|dev|test    # Delegates to apps/web-app"

# -------------------------
# Package delegation
# -------------------------

bootstrap:
    {{api_just}} bootstrap

api: _check_env
    {{api_just}} serve

migrate: _check_env
    {{api_just}} migrate

migration-revision message: _check_env
    {{api_just}} migration-revision "{{message}}"

backend-lint:
    {{api_just}} lint

backend-typecheck:
    {{api_just}} typecheck

backend-test:
    {{api_just}} test

cli-lint:
    {{cli_just}} lint

cli-typecheck:
    {{cli_just}} typecheck

cli-test:
    {{cli_just}} test

contracts-lint:
    {{contracts_just}} lint

contracts-typecheck:
    {{contracts_just}} typecheck

contracts-test:
    {{contracts_just}} test

web-lint:
    {{web_just}} lint

web-typecheck:
    {{web_just}} typecheck

web-dev:
    {{web_just}} dev

web-test:
    {{web_just}} test

# -------------------------
# Aggregate quality gates
# -------------------------

lint-all:
    just backend-lint
    just cli-lint
    just contracts-lint
    just web-lint

typecheck-all:
    just backend-typecheck
    just cli-typecheck
    just contracts-typecheck
    just web-typecheck
# -------------------------
# Infra (compose)
# -------------------------

dev-up: _check_env
    {{env_runner}} -- bash -c '\
        set -euo pipefail; \
        cd ..; \
        python ops/observability/render_collector_config.py; \
        services="postgres redis"; \
        collector_msg=""; \
        if [ "${ENABLE_OTEL_COLLECTOR:-false}" = "true" ]; then \
            services="${services} otel-collector"; \
            collector_msg=" + otel-collector (ports ${OTEL_COLLECTOR_HTTP_PORT:-4318}/${OTEL_COLLECTOR_GRPC_PORT:-4317})"; \
        fi; \
        echo "Starting ${services}${collector_msg}"; \
        docker compose -f {{compose_file}} up -d ${services}; \
    '

dev-down: _check_env
    {{env_runner}} -- bash -c 'cd .. && docker compose -f {{compose_file}} down'

dev-logs: _check_env
    {{env_runner}} -- bash -c '\
        set -euo pipefail; \
        cd ..; \
        services="postgres redis"; \
        if [ "${ENABLE_OTEL_COLLECTOR:-false}" = "true" ]; then \
            services="${services} otel-collector"; \
        fi; \
        docker compose -f {{compose_file}} logs -f --tail=100 ${services}; \
    '

dev-ps: _check_env
    {{env_runner}} -- bash -c 'cd .. && docker compose -f {{compose_file}} ps'

# -------------------------
# MinIO (storage)
# -------------------------

storage-up: _check_env
    {{env_runner}} -- bash -c 'cd {{repo_root}} && docker compose -f {{minio_compose_file}} up -d minio'

storage-down: _check_env
    {{env_runner}} -- bash -c 'cd {{repo_root}} && docker compose -f {{minio_compose_file}} down'

storage-logs: _check_env
    {{env_runner}} -- bash -c 'cd {{repo_root}} && docker compose -f {{minio_compose_file}} logs -f --tail=200 minio'

# -------------------------
# Vault dev signer
# -------------------------

vault-up:
    @echo "Starting Vault dev signer on {{vault_dev_host_addr}}"
    VAULT_DEV_PORT={{vault_dev_port}} VAULT_DEV_ROOT_TOKEN_ID={{vault_dev_root_token_id}} docker compose -f {{vault_compose_file}} up -d
    VAULT_ADDR={{vault_dev_host_addr}} tools/vault/wait-for-dev.sh
    HOST_VAULT_ADDR={{vault_dev_host_addr}} VAULT_DEV_ROOT_TOKEN_ID={{vault_dev_root_token_id}} VAULT_TRANSIT_KEY={{vault_transit_key}} docker compose -f {{vault_compose_file}} exec vault-dev /vault/dev-init.sh

vault-down:
    docker compose -f {{vault_compose_file}} down

vault-logs:
    docker compose -f {{vault_compose_file}} logs -f --tail=200

verify-vault: vault-up _check_env
    @echo "Running service-account issuance via starter CLI (ensure FastAPI is reachable)."
    VAULT_ADDR={{vault_dev_host_addr}} \
    VAULT_TOKEN={{vault_dev_root_token_id}} \
    VAULT_TRANSIT_KEY={{vault_transit_key}} \
    VAULT_VERIFY_ENABLED=true \
    {{env_runner}} -- bash -lc 'python -m starter_cli.app auth tokens issue-service-account --account dev-automation --scopes conversations:read --output text'

# -------------------------
# CLI helpers
# -------------------------

stripe-replay args: _check_env
    {{env_runner}} -- bash -lc 'python -m starter_cli.app stripe dispatches {{args}}'

stripe-listen:
    cd packages/starter_cli && hatch run python -m starter_cli.app stripe webhook-secret

lint-stripe-fixtures:
    cd packages/starter_cli && hatch run python -m starter_cli.app stripe dispatches validate-fixtures

test-stripe: _check_env
    {{env_runner}} -- bash -lc 'cd apps/api-service && hatch run pytest -m stripe_replay'

cli cmd:
    cd packages/starter_cli && hatch run python -m starter_cli.app {{cmd}}

doctor: _check_env
    {{env_runner}} -- bash -lc 'python -m starter_cli.app doctor --strict --json var/reports/operator-dashboard.json --markdown var/reports/operator-dashboard.md'

start-dev: _check_env
    {{env_runner}} -- bash -lc 'python -m starter_cli.app start dev --timeout 180'

start-backend: _check_env
    {{env_runner}} -- bash -lc 'python -m starter_cli.app start backend --timeout 120'

start-frontend: _check_env
    {{env_runner}} -- bash -lc 'python -m starter_cli.app start frontend --timeout 120'

# Wizards & seeding

setup-local-lite:
    cd packages/starter_cli && hatch run python -m starter_cli.app infra deps
    cd packages/starter_cli && hatch run python -m starter_cli.app setup wizard \
        --profile local \
        --auto-infra \
        --auto-secrets \
        --auto-migrations \
        --auto-redis \
        --no-auto-geoip \
        --auto-dev-user
    cd packages/starter_cli && hatch run python -m starter_cli.app users ensure-dev
    @echo "" && echo "Next: run 'just api' in a new terminal; optionally 'just issue-demo-token' after API is up."

setup-local-full:
    cd packages/starter_cli && hatch run python -m starter_cli.app infra deps
    cd packages/starter_cli && hatch run python -m starter_cli.app setup wizard \
        --profile local \
        --auto-infra \
        --auto-secrets \
        --auto-migrations \
        --auto-redis \
        --auto-geoip \
        --auto-stripe \
        --auto-dev-user

setup-staging:
    cd packages/starter_cli && hatch run python -m starter_cli.app infra deps
    cd packages/starter_cli && hatch run python -m starter_cli.app setup wizard \
        --profile staging \
        --no-auto-infra \
        --no-auto-secrets \
        --auto-migrations \
        --auto-redis \
        --auto-geoip \
        {{staging_answer_flags}}

setup-production:
    @if [ -z "{{setup_production_answers}}" ]; then \
        echo "Error: set setup_production_answers=/absolute/path/to/answers.json"; \
        exit 1; \
    fi
    cd packages/starter_cli && hatch run python -m starter_cli.app infra deps
    cd packages/starter_cli && hatch run python -m starter_cli.app setup wizard \
        --profile production \
        --strict \
        --answers-file {{setup_production_answers}} \
        --no-auto-infra \
        --no-auto-secrets \
        --auto-migrations \
        --auto-redis \
        --auto-geoip

seed-dev-user: dev-up _check_env
    {{env_runner}} -- bash -c ' \
        set -euo pipefail; \
        cd ..; \
        cmd=(python -m starter_cli.app users seed \
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

issue-demo-token:
    @echo "Ensure FastAPI is running (e.g., 'just api') before issuing a token."
    cd packages/starter_cli && hatch run python -m starter_cli.app auth tokens issue-service-account \
        --account "{{setup_service_account}}" \
        --scopes "{{setup_service_scopes}}" \
        {{service_tenant_flag}} \
        --output json
