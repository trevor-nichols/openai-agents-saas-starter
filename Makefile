SHELL := /bin/bash

# Select the application env file: prefer .env.local, fall back to .env.
ENV_FILE := $(word 1,$(wildcard .env.local .env))
ifeq ($(ENV_FILE),)
$(error No .env.local or .env file found. Create one before running make targets.)
endif

ENV_RUNNER := python scripts/run_with_env.py

.PHONY: help bootstrap api migrate migration-revision dev-up dev-down dev-logs dev-ps cli

help:
	@echo "Available commands:"
	@echo "  make dev-up                 # Start Postgres + Redis using .env.compose and $(ENV_FILE)"
	@echo "  make dev-down               # Stop the infrastructure stack"
	@echo "  make dev-logs               # Tail Postgres/Redis logs"
	@echo "  make dev-ps                 # Show running containers"
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
