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

.PHONY: help bootstrap api migrate migration-revision dev-up dev-down dev-logs dev-ps vault-up vault-down vault-logs verify-vault cli

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
	@echo "  make cli CMD='...'          # Run the consolidated operator CLI (python -m starter_cli.cli)"

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
	@$(ENV_RUNNER) .env.compose $(ENV_FILE) -- bash -c \
		'echo "Starting postgres (port $$POSTGRES_PORT) and redis (port $$REDIS_PORT)"; \
		docker compose up -d postgres redis'

dev-down:
	@$(ENV_RUNNER) .env.compose $(ENV_FILE) -- docker compose down

dev-logs:
	@$(ENV_RUNNER) .env.compose $(ENV_FILE) -- docker compose logs -f --tail=100 postgres redis

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
		$(ENV_RUNNER) .env.compose $(ENV_FILE) -- python -m starter_cli.cli auth tokens issue-service-account --account dev-automation --scopes conversations:read --output text

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

cli:
	@python -m starter_cli.cli $(CMD)
