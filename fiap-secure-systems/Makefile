SHELL := /usr/bin/env bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help

COMPOSE      := docker compose
COMPOSE_OBS  := docker compose -f docker-compose.yml -f docker-compose.observability.yml

.PHONY: help
help: ## Show this help
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: env-check
env-check: ## Verify .env exists, copying from .env.example if missing
	@if [ ! -f .env ]; then cp .env.example .env && echo "Created .env from .env.example"; fi

.PHONY: up
up: env-check ## Start core infra (postgres, localstack, otel-collector)
	$(COMPOSE) up -d

.PHONY: up-obs
up-obs: env-check ## Start core infra + observability stack
	$(COMPOSE_OBS) up -d

.PHONY: down
down: ## Stop and remove containers (volumes preserved)
	$(COMPOSE_OBS) down

.PHONY: nuke
nuke: ## Stop containers AND remove volumes (DESTRUCTIVE)
	$(COMPOSE_OBS) down -v

.PHONY: logs
logs: ## Tail logs for all running services
	$(COMPOSE_OBS) logs -f --tail=100

.PHONY: ps
ps: ## Show status of all stack containers
	@$(COMPOSE_OBS) ps

.PHONY: smoke
smoke: ## Verify the running infrastructure stack
	@./infrastructure/smoke/check-stack.sh

.PHONY: clean
clean: ## Remove local caches & build artifacts (does not stop containers)
	@find . -type d -name __pycache__ -prune -exec rm -rf {} +
	@find . -type d -name .pytest_cache -prune -exec rm -rf {} +
	@find . -type d -name build -prune -exec rm -rf {} +
	@find . -type d -name target -prune -exec rm -rf {} +
	@echo "Cleaned local caches."
