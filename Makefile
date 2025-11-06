SHELL := /bin/bash

# Select the environment file: prefer .env.local, fall back to .env.
ENV_FILE := $(word 1,$(wildcard .env.local .env))
ifeq ($(ENV_FILE),)
$(error No .env.local or .env file found. Create one before running make targets.)
endif

.PHONY: help migrate migration-revision

help:
	@echo "Available commands:"
	@echo "  make migrate                # Run Alembic migrations using env vars from $(ENV_FILE)"
	@echo "  make migration-revision MESSAGE=...  # Create a new Alembic revision with the given message"

migrate:
	@echo "Using environment file: $(ENV_FILE)"
	@set -a; . $(ENV_FILE); set +a; hatch run migrate

migration-revision:
	@if [ -z "$(MESSAGE)" ]; then \
		echo "MESSAGE variable is required, e.g. make migration-revision MESSAGE=add_users"; \
		exit 1; \
	fi
	@echo "Using environment file: $(ENV_FILE)"
	@set -a; . $(ENV_FILE); set +a; hatch run migration-revision "$(MESSAGE)"
