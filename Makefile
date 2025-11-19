SHELL := /bin/bash

# Select the application env file: prefer .env.local, fall back to .env.
ENV_FILE := $(word 1,$(wildcard .env.local .env))
ifeq ($(ENV_FILE),)
$(error No .env.local or .env file found. Create one before running make targets.)
endif

ENV_RUNNER := python scripts/run_with_env.py
VAULT_DEV_COMPOSE ?= docker compose -f docker-compose.vault-dev.yml
VAULT_DEV_PORT ?= 18200
VAULT_DEV_ROOT_TOKEN_ID ?= vault-dev-root
VAULT_DEV_HOST_ADDR ?= http://127.0.0.1:$(VAULT_DEV_PORT)
VAULT_TRANSIT_KEY ?= auth-service

# Starter CLI setup helpers
SETUP_USER_EMAIL ?= dev@example.com
SETUP_USER_NAME ?= Dev Admin
SETUP_USER_PASSWORD ?=
SETUP_USER_TENANT ?= default
SETUP_USER_TENANT_NAME ?= Default Tenant
SETUP_USER_ROLE ?= admin
SETUP_SERVICE_ACCOUNT ?= demo-bot
SETUP_SERVICE_SCOPES ?= chat:write,conversations:read
SETUP_SERVICE_TENANT ?=
SETUP_STAGING_ANSWERS ?=
SETUP_PRODUCTION_ANSWERS ?=
STAGING_ANSWER_FLAGS := $(if $(strip $(SETUP_STAGING_ANSWERS)), --non-interactive --answers-file $(SETUP_STAGING_ANSWERS))
SERVICE_TENANT_FLAG := $(if $(strip $(SETUP_SERVICE_TENANT)), --tenant $(SETUP_SERVICE_TENANT))

.PHONY: help bootstrap api migrate migration-revision dev-up dev-down dev-logs dev-ps vault-up vault-down vault-logs verify-vault cli setup-local-lite setup-local-full setup-staging setup-production seed-dev-user issue-demo-token

help:
	@echo "Available commands:"
	@echo "  make dev-up                 # Start Postgres + Redis using .env.compose and $(ENV_FILE)"
	@echo "  make dev-down               # Stop the infrastructure stack"
	@echo "  make dev-logs               # Tail Postgres/Redis logs"
	@echo "  make dev-ps                 # Show running containers"
	@echo "  make vault-up               # Start the local Vault dev signer"
	@echo "  make vault-down             # Stop the local Vault dev signer"
	@echo "  make vault-logs             # Tail logs for the dev Vault container"
	@echo "  make verify-vault           # Spin up Vault dev + run CLI issuance smoke test"
	@echo "  make migrate                # Run Alembic migrations with current env"
	@echo "  make migration-revision MESSAGE=...  # Create a new Alembic revision"
	@echo "  make bootstrap              # Provision the Hatch environment with project dependencies"
	@echo "  make api                    # Run the FastAPI server via hatch run serve"
	@echo "  make test-stripe            # Run fixture-driven Stripe replay tests"
	@echo "  make stripe-replay ARGS='...' # Invoke the Stripe replay CLI"
	@echo "  make lint-stripe-fixtures   # Validate Stripe fixture JSON files"
	@echo "  make cli-verify-env         # Check docs/trackers/CLI_ENV_INVENTORY.md vs runtime settings"
	@echo "  make validate-providers     # Validate Stripe/Resend/Tavily env configuration"
	@echo "  make cli CMD='...'          # Run the consolidated operator CLI (python -m starter_cli.app)"
	@echo "  make setup-local-lite       # Run Starter CLI wizard with Local-Lite defaults + seed a dev user"
	@echo "  make setup-local-full       # Run Starter CLI wizard with Local-Full automation toggles"
	@echo "  make setup-staging          # Run Starter CLI wizard with staging-safe automation"
	@echo "  make setup-production SETUP_PRODUCTION_ANSWERS=path/to.json"
	@echo "                              # Headless production-ready wizard run"
	@echo "  make seed-dev-user          # Ensure Compose is up and seed a developer account"
	@echo "  make issue-demo-token       # Issue a service-account refresh token (requires API running)"

bootstrap:
	@echo "Creating/refreshing the Hatch environment"
	@hatch env create

api:
	@echo "Starting FastAPI via hatch run serve"
	@$(ENV_RUNNER) .env.compose $(ENV_FILE) -- hatch run serve

migrate:
	@echo "Using .env.compose + $(ENV_FILE)"
	@$(ENV_RUNNER) .env.compose $(ENV_FILE) -- hatch run migrate


migration-revision:
	@if [ -z "$(MESSAGE)" ]; then \
		echo "MESSAGE variable is required, e.g. make migration-revision MESSAGE=add_users"; \
		exit 1; \
	fi
	@echo "Using .env.compose + $(ENV_FILE)"
	@$(ENV_RUNNER) .env.compose $(ENV_FILE) -- hatch run migration-revision "$(MESSAGE)"

dev-up:
	@$(ENV_RUNNER) .env.compose $(ENV_FILE) -- python ops/observability/render_collector_config.py
	@$(ENV_RUNNER) .env.compose $(ENV_FILE) -- bash -c '
		set -euo pipefail;
		services="postgres redis";
		collector_msg="";
		if [ "$${ENABLE_OTEL_COLLECTOR:-false}" = "true" ]; then 
			services="$${services} otel-collector";
			collector_msg=" + otel-collector (ports $${OTEL_COLLECTOR_HTTP_PORT:-4318}/$${OTEL_COLLECTOR_GRPC_PORT:-4317})";
		fi;
		echo "Starting $${services}${collector_msg}";
		docker compose up -d $${services};
	'

dev-down:
	@$(ENV_RUNNER) .env.compose $(ENV_FILE) -- docker compose down

dev-logs:
	@$(ENV_RUNNER) .env.compose $(ENV_FILE) -- bash -c '
		services="postgres redis";
		if [ "$${ENABLE_OTEL_COLLECTOR:-false}" = "true" ]; then 
			services="$${services} otel-collector";
		fi;
		docker compose logs -f --tail=100 $${services};
	'

dev-ps:
	@$(ENV_RUNNER) .env.compose $(ENV_FILE) -- docker compose ps

vault-up:
	@echo "Starting Vault dev signer on $(VAULT_DEV_HOST_ADDR)"
	@VAULT_DEV_PORT=$(VAULT_DEV_PORT) VAULT_DEV_ROOT_TOKEN_ID=$(VAULT_DEV_ROOT_TOKEN_ID) $(VAULT_DEV_COMPOSE) up -d
	@VAULT_ADDR=$(VAULT_DEV_HOST_ADDR) scripts/vault/wait-for-dev.sh
	@HOST_VAULT_ADDR=$(VAULT_DEV_HOST_ADDR) VAULT_DEV_ROOT_TOKEN_ID=$(VAULT_DEV_ROOT_TOKEN_ID) VAULT_TRANSIT_KEY=$(VAULT_TRANSIT_KEY) $(VAULT_DEV_COMPOSE) exec vault-dev /vault/dev-init.sh

vault-down:
	@$(VAULT_DEV_COMPOSE) down

vault-logs:
	@$(VAULT_DEV_COMPOSE) logs -f --tail=200

verify-vault: vault-up
	@echo "Running service-account issuance via starter CLI (ensure FastAPI is reachable)."
	@VAULT_ADDR=$(VAULT_DEV_HOST_ADDR) \
		VAULT_TOKEN=$(VAULT_DEV_ROOT_TOKEN_ID) \
		VAULT_TRANSIT_KEY=$(VAULT_TRANSIT_KEY) \
		VAULT_VERIFY_ENABLED=true \
		$(ENV_RUNNER) .env.compose $(ENV_FILE) -- python -m starter_cli.app auth tokens issue-service-account --account dev-automation --scopes conversations:read --output text

test-stripe:
	@$(ENV_RUNNER) .env.compose $(ENV_FILE) -- hatch run pytest -m stripe_replay

stripe-replay:
	@if [ -z "$(ARGS)" ]; then \
		echo "Usage: make stripe-replay ARGS='list --status failed'"; \
		exit 1; \
	fi
	@$(ENV_RUNNER) .env.compose $(ENV_FILE) -- python scripts/stripe/replay_events.py $(ARGS)

lint-stripe-fixtures:
	@python scripts/stripe/replay_events.py validate-fixtures

cli-verify-env:
	@python -m scripts.cli.verify_env_inventory

validate-providers:
	@python -m starter_cli.app providers validate

cli:
	@python -m starter_cli.app $(CMD)

setup-local-lite:
	@python -m starter_cli.app infra deps
	@python -m starter_cli.app setup wizard \
		--profile local \
		--auto-infra \
		--auto-secrets \
		--auto-migrations \
		--auto-redis \
		--no-auto-geoip
	@$(MAKE) seed-dev-user
	@echo ""
	@echo "Next steps:"
	@echo "  1. Run 'make api' in a new terminal to start FastAPI."
	@echo "  2. Once the API is up, run 'make issue-demo-token' to mint a service-account token."

setup-local-full:
	@python -m starter_cli.app infra deps
	@python -m starter_cli.app setup wizard \
		--profile local \
		--auto-infra \
		--auto-secrets \
		--auto-migrations \
		--auto-redis \
		--auto-geoip \
		--auto-stripe
	@$(MAKE) seed-dev-user
	@echo ""
	@echo "Local-Full ready. Start FastAPI with 'make api' and run 'make issue-demo-token' if needed."

setup-staging:
	@python -m starter_cli.app infra deps
	@python -m starter_cli.app setup wizard \
		--profile staging \
		--no-auto-infra \
		--no-auto-secrets \
		--auto-migrations \
		--auto-redis \
		--auto-geoip $(STAGING_ANSWER_FLAGS)

setup-production:
	@if [ -z "$(strip $(SETUP_PRODUCTION_ANSWERS))" ]; then \
		echo "Error: set SETUP_PRODUCTION_ANSWERS=/absolute/path/to/answers.json"; \
		exit 1; \
	fi
	@python -m starter_cli.app infra deps
	@python -m starter_cli.app setup wizard \
		--profile production \
		--strict \
		--answers-file $(SETUP_PRODUCTION_ANSWERS) \
		--no-auto-infra \
		--no-auto-secrets \
		--auto-migrations \
		--auto-redis \
		--auto-geoip

seed-dev-user: dev-up
	@$(ENV_RUNNER) .env.compose $(ENV_FILE) -- bash -c " \
		set -euo pipefail; \
		cmd=(python scripts/seed_users.py \
			--email \"$(SETUP_USER_EMAIL)\" \
			--tenant-slug \"$(SETUP_USER_TENANT)\" \
			--tenant-name \"$(SETUP_USER_TENANT_NAME)\" \
			--role \"$(SETUP_USER_ROLE)\" \
			--display-name \"$(SETUP_USER_NAME)\"); \
		if [ -n \"$(SETUP_USER_PASSWORD)\" ]; then \
			cmd+=(--password \"$(SETUP_USER_PASSWORD)\"); \
		fi; \
		echo \"Seeding user with email $(SETUP_USER_EMAIL)\"; \
		\"$${cmd[@]}\"; \
	"

issue-demo-token:
	@echo "Ensure FastAPI is running (e.g., 'make api') before issuing a token."
	@python -m starter_cli.app auth tokens issue-service-account \
		--account "$(SETUP_SERVICE_ACCOUNT)" \
		--scopes "$(SETUP_SERVICE_SCOPES)"$(SERVICE_TENANT_FLAG) \
		--output json
