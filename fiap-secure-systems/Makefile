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

# === smart-service ===

.PHONY: smart-sync
smart-sync: ## (smart-service) install/sync deps via uv
	cd smart-service && uv sync

.PHONY: smart-test-unit
smart-test-unit: ## (smart-service) run unit tests only
	cd smart-service && uv run pytest -m "not integration"

.PHONY: smart-test-integration
smart-test-integration: ## (smart-service) run integration tests (Docker required)
	cd smart-service && uv run pytest -m "integration"

.PHONY: smart-lint
smart-lint: ## (smart-service) ruff + mypy
	cd smart-service && uv run ruff check . && uv run mypy smart_service

.PHONY: smart-up
smart-up: env-check ## (smart-service) start core infra + smart-service
	$(COMPOSE) up -d smart-service

.PHONY: smart-logs
smart-logs: ## (smart-service) tail smart-service logs
	$(COMPOSE) logs -f --tail=100 smart-service

.PHONY: smart-shell
smart-shell: ## (smart-service) exec a shell inside the running smart-service
	docker exec -it fss-smart-service /bin/sh

.PHONY: round-trip
round-trip: ## (smart-service) end-to-end synthetic SQS round-trip (requires stack up)
	@./infrastructure/smoke/round-trip.sh

# === orchestrator-service ===

.PHONY: orch-build
orch-build: ## (orchestrator-service) compile + bootJar
	./gradlew :orchestrator-service:bootJar

.PHONY: orch-test-unit
orch-test-unit: ## (orchestrator-service) run unit tests only
	./gradlew :orchestrator-service:test

.PHONY: orch-test-integration
orch-test-integration: ## (orchestrator-service) run integration tests (Docker required)
	./gradlew :orchestrator-service:integrationTest

.PHONY: orch-up
orch-up: env-check ## (orchestrator-service) start core infra + smart-service + orchestrator-service
	$(COMPOSE) up -d orchestrator-service

.PHONY: orch-logs
orch-logs: ## (orchestrator-service) tail orchestrator-service logs
	$(COMPOSE) logs -f --tail=100 orchestrator-service

.PHONY: orch-shell
orch-shell: ## (orchestrator-service) exec a shell inside the running orchestrator-service
	docker exec -it fss-orchestrator-service /bin/sh

.PHONY: orch-round-trip
orch-round-trip: ## (orchestrator-service) end-to-end session lifecycle (requires stack up)
	@./infrastructure/smoke/orchestrator-round-trip.sh

# === gateway-service ===

.PHONY: gw-build
gw-build: ## (gateway-service) compile + bootJar
	./gradlew :gateway-service:bootJar

.PHONY: gw-test-unit
gw-test-unit: ## (gateway-service) run unit tests only
	./gradlew :gateway-service:test

.PHONY: gw-test-integration
gw-test-integration: ## (gateway-service) run integration tests (Docker required)
	./gradlew :gateway-service:integrationTest

.PHONY: gw-up
gw-up: env-check gen-jwt-keys ## (gateway-service) start full stack with gateway-service
	$(COMPOSE) up -d gateway-service

.PHONY: gw-logs
gw-logs: ## (gateway-service) tail gateway-service logs
	$(COMPOSE) logs -f --tail=100 gateway-service

.PHONY: gw-shell
gw-shell: ## (gateway-service) exec a shell inside the running gateway-service
	docker exec -it fss-gateway-service /bin/sh

.PHONY: gw-round-trip
gw-round-trip: ## (gateway-service) end-to-end register → finalize → REPORT_READY (requires stack up)
	@./infrastructure/smoke/gateway-round-trip.sh

.PHONY: gen-jwt-keys
gen-jwt-keys: ## Generate RS256 JWT keys for gateway-service (no-op if already present)
	@if [ ! -f infrastructure/jwt/jwt-private.pem ]; then \
	  mkdir -p infrastructure/jwt; \
	  openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out infrastructure/jwt/jwt-private.pem; \
	  openssl rsa -in infrastructure/jwt/jwt-private.pem -pubout -out infrastructure/jwt/jwt-public.pem; \
	  echo "[gen-jwt-keys] wrote infrastructure/jwt/jwt-{private,public}.pem"; \
	else echo "[gen-jwt-keys] keys already exist; skipping"; fi

# === frontend ===

.PHONY: front-build
front-build: ## (frontend) install deps + production build
	cd frontend && npm ci && npm run build

.PHONY: front-test
front-test: ## (frontend) Vitest unit tests
	cd frontend && npm ci && npm test -- --run

.PHONY: front-dev
front-dev: ## (frontend) start Vite dev server (no docker)
	cd frontend && npm install && npm run dev

.PHONY: front-up
front-up: env-check ## (frontend) start full stack with frontend container
	$(COMPOSE) up -d frontend

.PHONY: front-logs
front-logs: ## (frontend) tail frontend container logs
	$(COMPOSE) logs -f --tail=100 frontend

.PHONY: front-shell
front-shell: ## (frontend) exec a shell inside the running frontend container
	docker exec -it fss-frontend /bin/sh

.PHONY: front-round-trip
front-round-trip: ## (frontend) end-to-end public flow via curl + wscat (requires stack up)
	@./infrastructure/smoke/front-round-trip.sh
