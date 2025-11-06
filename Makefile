SHELL := /bin/bash

# Select the application env file: prefer .env.local, fall back to .env.
ENV_FILE := $(word 1,$(wildcard .env.local .env))
ifeq ($(ENV_FILE),)
$(error No .env.local or .env file found. Create one before running make targets.)
endif

ENV_RUNNER := python scripts/run_with_env.py

.PHONY: help migrate migration-revision dev-up dev-down dev-logs dev-ps

help:
	@echo "Available commands:"
	@echo "  make dev-up                 # Start Postgres + Redis using .env.compose and $(ENV_FILE)"
	@echo "  make dev-down               # Stop the infrastructure stack"
	@echo "  make dev-logs               # Tail Postgres/Redis logs"
	@echo "  make dev-ps                 # Show running containers"
	@echo "  make migrate                # Run Alembic migrations with current env"
	@echo "  make migration-revision MESSAGE=...  # Create a new Alembic revision"

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
