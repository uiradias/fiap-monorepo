# Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the repo skeleton, docker-compose stack (Postgres + LocalStack + observability), and shared JSON-schema contracts so the three application services can be developed against a working local infrastructure.

**Architecture:** Single git repo at `/Users/uiradias/Repository/fiap-monorepo/fiap-secure-systems` (subdirectory inside the existing `fiap-monorepo` git repo). All infra is declarative — `docker-compose.yml` provides the runtime; `infrastructure/` holds init scripts, OTel/observability configs, and JSON schemas. The plan is verification-driven: each task ends with a concrete shell command whose expected output is shown.

**Tech Stack:** Docker + docker-compose v2, Postgres 16, LocalStack 3, OTel Collector (contrib), Tempo 2, Prometheus 2.51, Loki 3, Grafana 10, GNU Make, JSON Schema (draft-07).

**Working directory for all paths in this plan:** `/Users/uiradias/Repository/fiap-monorepo/fiap-secure-systems`

**Definition of done for this plan:**
1. `make up` brings up Postgres, LocalStack, and the OTel Collector cleanly.
2. `make up-obs` brings up Tempo, Prometheus, Loki, Grafana on top of `make up`.
3. `make smoke` runs and prints `OK` for every check (3 DBs exist; 1 S3 bucket exists; 1 SNS topic exists; 4 SQS queues + their DLQs exist; SNS topic is subscribed to the gateway queue; OTel collector accepts OTLP/gRPC on :4317).
4. Four JSON schemas exist under `infrastructure/contracts/` and are valid JSON Schema draft-07.
5. Every task in this plan ends in its own commit.

---

## Resource inventory (locked by this plan)

| Resource | Name | Purpose |
|---|---|---|
| Postgres DB | `gateway_db` | gateway-service ownership |
| Postgres DB | `orchestrator_db` | orchestrator-service ownership |
| Postgres DB | `smart_db` | smart-service ownership |
| S3 bucket | `fiap-secure-systems-assets` | uploaded asset storage |
| SNS topic | `session-events` | orchestrator → gateway fan-out |
| SQS queue | `analysis-jobs` | orchestrator → smart-service work |
| SQS queue | `analysis-jobs-dlq` | DLQ for above |
| SQS queue | `analysis-results` | smart-service → orchestrator results |
| SQS queue | `analysis-results-dlq` | DLQ for above |
| SQS queue | `session-events-gateway` | per-gateway-replica fan-out target |
| SQS queue | `session-events-gateway-dlq` | DLQ for above |
| Subscription | SNS `session-events` → SQS `session-events-gateway` | event fan-out |

DLQ policies: 3 receives → DLQ.

---

## File map (created by this plan)

```
fiap-secure-systems/
├── .env.example                                 (Task 1)
├── .gitignore                                   (Task 1)
├── README.md                                    (Task 9)
├── Makefile                                     (Task 2, extended through 8)
├── docker-compose.yml                           (Task 5, extended through 6)
├── docker-compose.observability.yml             (Task 6)
├── infrastructure/
│   ├── postgres/init/01-create-databases.sql    (Task 3)
│   ├── localstack/init/01-bootstrap.sh          (Task 4)
│   ├── otel/
│   │   ├── otel-collector-config.yaml           (Task 6)
│   │   ├── tempo.yaml                           (Task 6)
│   │   ├── prometheus.yml                       (Task 6)
│   │   ├── loki.yaml                            (Task 6)
│   │   └── grafana/provisioning/datasources/datasources.yaml  (Task 6)
│   ├── contracts/
│   │   ├── analysis-jobs.schema.json            (Task 7)
│   │   ├── analysis-results.schema.json         (Task 7)
│   │   ├── session-events.schema.json           (Task 7)
│   │   └── analysis-report.schema.json          (Task 7)
│   └── smoke/check-stack.sh                     (Task 8)
└── docs/superpowers/
    ├── specs/2026-05-05-fiap-secure-systems-design.md   (already exists)
    └── plans/2026-05-06-foundation.md                   (this file)
```

---

## Task 1: Repo skeleton + .gitignore + .env.example

**Files:**
- Create: `fiap-secure-systems/.gitignore`
- Create: `fiap-secure-systems/.env.example`
- Create empty directories (with `.gitkeep`): `infrastructure/postgres/init/`, `infrastructure/localstack/init/`, `infrastructure/otel/grafana/provisioning/datasources/`, `infrastructure/contracts/`, `infrastructure/smoke/`

- [ ] **Step 1: Create the directory tree**

```bash
cd /Users/uiradias/Repository/fiap-monorepo/fiap-secure-systems
mkdir -p infrastructure/postgres/init \
         infrastructure/localstack/init \
         infrastructure/otel/grafana/provisioning/datasources \
         infrastructure/contracts \
         infrastructure/smoke
touch infrastructure/postgres/init/.gitkeep \
      infrastructure/localstack/init/.gitkeep \
      infrastructure/otel/grafana/provisioning/datasources/.gitkeep \
      infrastructure/contracts/.gitkeep \
      infrastructure/smoke/.gitkeep
```

- [ ] **Step 2: Write `.gitignore`**

File: `fiap-secure-systems/.gitignore`

```gitignore
# Environment
.env
.env.local
.env.*.local

# Volumes & runtime
.localstack/
postgres-data/
grafana-data/

# OS
.DS_Store

# IDEs
.idea/
.vscode/
*.iml

# Build artifacts (will appear once services are added)
**/build/
**/target/
**/dist/
**/node_modules/
**/.gradle/
**/__pycache__/
**/.pytest_cache/
**/.venv/
*.pyc

# Logs
*.log
```

- [ ] **Step 3: Write `.env.example`**

File: `fiap-secure-systems/.env.example`

```env
# === LocalStack / AWS SDK ===
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_ENDPOINT_URL=http://localstack:4566

# Resource names (also defined in compose; here for app services)
S3_BUCKET=fiap-secure-systems-assets
SNS_TOPIC_SESSION_EVENTS=arn:aws:sns:us-east-1:000000000000:session-events
SQS_ANALYSIS_JOBS_URL=http://localstack:4566/000000000000/analysis-jobs
SQS_ANALYSIS_RESULTS_URL=http://localstack:4566/000000000000/analysis-results
SQS_SESSION_EVENTS_GATEWAY_URL=http://localstack:4566/000000000000/session-events-gateway

# === Postgres ===
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
GATEWAY_DB=gateway_db
ORCHESTRATOR_DB=orchestrator_db
SMART_DB=smart_db

# === Observability ===
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
OTEL_EXPORTER_OTLP_PROTOCOL=grpc

# === Service-specific (filled in later sub-plans) ===
ANTHROPIC_API_KEY=          # smart-service only; never commit a real value
INTERNAL_HMAC_SECRET=change-me-32-bytes-min-for-real-deployments
JWT_PRIVATE_KEY_PATH=        # gateway-service only; generated locally
JWT_PUBLIC_KEY_PATH=         # gateway-service only; generated locally
```

- [ ] **Step 4: Verify file presence**

```bash
cd /Users/uiradias/Repository/fiap-monorepo/fiap-secure-systems
ls -la .gitignore .env.example
find infrastructure -type d
```

Expected:
```
.gitignore
.env.example
infrastructure
infrastructure/postgres
infrastructure/postgres/init
infrastructure/localstack
infrastructure/localstack/init
infrastructure/otel
infrastructure/otel/grafana
infrastructure/otel/grafana/provisioning
infrastructure/otel/grafana/provisioning/datasources
infrastructure/contracts
infrastructure/smoke
```

- [ ] **Step 5: Commit**

```bash
cd /Users/uiradias/Repository/fiap-monorepo
git add fiap-secure-systems/.gitignore \
        fiap-secure-systems/.env.example \
        fiap-secure-systems/infrastructure
git commit -m "chore(fiap-secure-systems): initial repo skeleton"
```

---

## Task 2: Makefile foundation

**Files:**
- Create: `fiap-secure-systems/Makefile`

- [ ] **Step 1: Write the Makefile**

File: `fiap-secure-systems/Makefile`

```makefile
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

.PHONY: smoke
smoke: ## Run the foundation smoke check (added in Task 8)
	@echo "smoke target not yet implemented (Task 8)"; exit 1

.PHONY: clean
clean: ## Remove local caches & build artifacts (does not stop containers)
	@find . -type d -name __pycache__ -prune -exec rm -rf {} +
	@find . -type d -name .pytest_cache -prune -exec rm -rf {} +
	@find . -type d -name build -prune -exec rm -rf {} +
	@find . -type d -name target -prune -exec rm -rf {} +
	@echo "Cleaned local caches."
```

- [ ] **Step 2: Run `make help` to verify**

```bash
cd /Users/uiradias/Repository/fiap-monorepo/fiap-secure-systems
make help
```

Expected: prints a list of targets (`help`, `env-check`, `up`, `up-obs`, `down`, `nuke`, `logs`, `smoke`, `clean`).

- [ ] **Step 3: Run `make env-check` to verify it copies the .env**

```bash
make env-check
ls -la .env
```

Expected: `.env` file now exists, identical to `.env.example`.

- [ ] **Step 4: Run `make smoke` to confirm it currently exits 1 (placeholder)**

```bash
make smoke || echo "exited non-zero, as expected"
```

Expected: prints `smoke target not yet implemented (Task 8)` and `exited non-zero, as expected`.

- [ ] **Step 5: Commit**

```bash
cd /Users/uiradias/Repository/fiap-monorepo
git add fiap-secure-systems/Makefile
git commit -m "chore(fiap-secure-systems): add Makefile with help/up/down/nuke/smoke targets"
```

---

## Task 3: Postgres init script + compose service + verification

**Files:**
- Create: `fiap-secure-systems/infrastructure/postgres/init/01-create-databases.sql`
- Create: `fiap-secure-systems/docker-compose.yml` (Postgres section)

- [ ] **Step 1: Write the init SQL**

File: `fiap-secure-systems/infrastructure/postgres/init/01-create-databases.sql`

```sql
-- Runs once on a fresh Postgres data directory (mounted at /docker-entrypoint-initdb.d).
-- Creates one logical database per service, all owned by the default postgres user.
-- Service-specific schemas/migrations are managed by Flyway/Alembic in each service.

CREATE DATABASE gateway_db;
CREATE DATABASE orchestrator_db;
CREATE DATABASE smart_db;

-- Enable required extensions on each DB.
\connect gateway_db
CREATE EXTENSION IF NOT EXISTS citext;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

\connect orchestrator_db
CREATE EXTENSION IF NOT EXISTS pgcrypto;

\connect smart_db
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```

- [ ] **Step 2: Write the initial `docker-compose.yml` with only Postgres**

File: `fiap-secure-systems/docker-compose.yml`

```yaml
name: fiap-secure-systems

x-common-env: &common-env
  AWS_REGION: ${AWS_REGION}
  AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
  AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY}

services:
  postgres:
    image: postgres:16-alpine
    container_name: fss-postgres
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./infrastructure/postgres/init:/docker-entrypoint-initdb.d:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d postgres"]
      interval: 5s
      timeout: 5s
      retries: 10
    networks:
      - fss

volumes:
  postgres-data:

networks:
  fss:
    driver: bridge
    name: fss-network
```

- [ ] **Step 3: Bring postgres up**

```bash
cd /Users/uiradias/Repository/fiap-monorepo/fiap-secure-systems
make nuke   # ensure no stale volume from prior runs
make up
```

Expected: `Container fss-postgres  Started` (and only `fss-postgres` since other services aren't defined yet).

- [ ] **Step 4: Wait for healthy then verify the three DBs exist**

```bash
# Wait up to 30s for the healthcheck to flip
for i in {1..30}; do
  status=$(docker inspect -f '{{.State.Health.Status}}' fss-postgres)
  if [ "$status" = "healthy" ]; then break; fi
  sleep 1
done
echo "postgres status: $status"

docker exec fss-postgres psql -U postgres -tAc \
  "SELECT datname FROM pg_database WHERE datname IN ('gateway_db','orchestrator_db','smart_db') ORDER BY datname;"
```

Expected output (exactly):
```
postgres status: healthy
gateway_db
orchestrator_db
smart_db
```

- [ ] **Step 5: Verify extensions on each DB**

```bash
for db in gateway_db orchestrator_db smart_db; do
  echo "--- $db ---"
  docker exec fss-postgres psql -U postgres -d "$db" -tAc \
    "SELECT extname FROM pg_extension WHERE extname IN ('citext','pgcrypto') ORDER BY extname;"
done
```

Expected:
```
--- gateway_db ---
citext
pgcrypto
--- orchestrator_db ---
pgcrypto
--- smart_db ---
pgcrypto
```

- [ ] **Step 6: Tear down and commit**

```bash
make down
cd /Users/uiradias/Repository/fiap-monorepo
git add fiap-secure-systems/docker-compose.yml \
        fiap-secure-systems/infrastructure/postgres/init/01-create-databases.sql
git commit -m "feat(fiap-secure-systems): add postgres with three logical databases"
```

---

## Task 4: LocalStack init script + compose service + verification

**Files:**
- Create: `fiap-secure-systems/infrastructure/localstack/init/01-bootstrap.sh`
- Modify: `fiap-secure-systems/docker-compose.yml` (add `localstack` service)

- [ ] **Step 1: Write the bootstrap script**

LocalStack runs every executable file in `/etc/localstack/init/ready.d/` once it has finished booting. We use the `awslocal` CLI baked into the image.

File: `fiap-secure-systems/infrastructure/localstack/init/01-bootstrap.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

REGION="${AWS_REGION:-us-east-1}"
ACCOUNT="000000000000"

echo "[bootstrap] creating S3 bucket"
awslocal s3api create-bucket --bucket fiap-secure-systems-assets --region "$REGION" >/dev/null
awslocal s3api put-bucket-encryption \
  --bucket fiap-secure-systems-assets \
  --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}' >/dev/null

echo "[bootstrap] creating SNS topic"
TOPIC_ARN=$(awslocal sns create-topic --name session-events --query TopicArn --output text)
echo "[bootstrap] topic arn: $TOPIC_ARN"

create_queue () {
  local name="$1" dlq="$2"
  echo "[bootstrap] creating queue $name (dlq=$dlq)"
  local dlq_url dlq_arn
  awslocal sqs create-queue --queue-name "$dlq" >/dev/null
  dlq_url=$(awslocal sqs get-queue-url --queue-name "$dlq" --query QueueUrl --output text)
  dlq_arn=$(awslocal sqs get-queue-attributes --queue-url "$dlq_url" \
    --attribute-names QueueArn --query 'Attributes.QueueArn' --output text)
  awslocal sqs create-queue \
    --queue-name "$name" \
    --attributes "{\"VisibilityTimeout\":\"300\",\"RedrivePolicy\":\"{\\\"deadLetterTargetArn\\\":\\\"$dlq_arn\\\",\\\"maxReceiveCount\\\":\\\"3\\\"}\"}" \
    >/dev/null
}

create_queue analysis-jobs           analysis-jobs-dlq
create_queue analysis-results        analysis-results-dlq
create_queue session-events-gateway  session-events-gateway-dlq

echo "[bootstrap] subscribing session-events-gateway to SNS topic"
QUEUE_ARN=$(awslocal sqs get-queue-attributes \
  --queue-url "http://localhost:4566/${ACCOUNT}/session-events-gateway" \
  --attribute-names QueueArn --query 'Attributes.QueueArn' --output text)
awslocal sns subscribe \
  --topic-arn "$TOPIC_ARN" \
  --protocol sqs \
  --notification-endpoint "$QUEUE_ARN" \
  --attributes "RawMessageDelivery=true" >/dev/null

echo "[bootstrap] done"
```

- [ ] **Step 2: Make it executable**

```bash
cd /Users/uiradias/Repository/fiap-monorepo/fiap-secure-systems
chmod +x infrastructure/localstack/init/01-bootstrap.sh
```

- [ ] **Step 3: Add `localstack` service to compose**

Edit `fiap-secure-systems/docker-compose.yml` — append the `localstack` block under `services:` (keep `postgres` as-is). Final state of the file should be:

```yaml
name: fiap-secure-systems

x-common-env: &common-env
  AWS_REGION: ${AWS_REGION}
  AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
  AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY}

services:
  postgres:
    image: postgres:16-alpine
    container_name: fss-postgres
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./infrastructure/postgres/init:/docker-entrypoint-initdb.d:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d postgres"]
      interval: 5s
      timeout: 5s
      retries: 10
    networks: [fss]

  localstack:
    image: localstack/localstack:3.5
    container_name: fss-localstack
    environment:
      <<: *common-env
      SERVICES: s3,sns,sqs
      DEBUG: "0"
      PERSISTENCE: "0"
      LOCALSTACK_HOST: localstack
    ports:
      - "4566:4566"
    volumes:
      - ./infrastructure/localstack/init:/etc/localstack/init/ready.d:ro
      - /var/run/docker.sock:/var/run/docker.sock
    healthcheck:
      test: ["CMD-SHELL", "awslocal sqs get-queue-url --queue-name analysis-jobs >/dev/null 2>&1"]
      interval: 5s
      timeout: 5s
      retries: 30
      start_period: 20s
    networks: [fss]

volumes:
  postgres-data:

networks:
  fss:
    driver: bridge
    name: fss-network
```

- [ ] **Step 4: Bring it up and wait for both healthy**

```bash
cd /Users/uiradias/Repository/fiap-monorepo/fiap-secure-systems
make up

for svc in fss-postgres fss-localstack; do
  for i in {1..60}; do
    s=$(docker inspect -f '{{.State.Health.Status}}' "$svc" 2>/dev/null || echo none)
    [ "$s" = "healthy" ] && break
    sleep 1
  done
  echo "$svc: $s"
done
```

Expected:
```
fss-postgres: healthy
fss-localstack: healthy
```

- [ ] **Step 5: Verify the bucket, topic, queues, and subscription**

```bash
docker exec fss-localstack awslocal s3api list-buckets --query 'Buckets[].Name' --output text
docker exec fss-localstack awslocal sns list-topics --query 'Topics[].TopicArn' --output text
docker exec fss-localstack awslocal sqs list-queues --query 'QueueUrls[]' --output text | tr '\t' '\n' | sort
docker exec fss-localstack awslocal sns list-subscriptions --query 'Subscriptions[].{Protocol:Protocol,Endpoint:Endpoint}' --output text
```

Expected (paths may show `localhost` vs container hostname depending on LocalStack version):
```
fiap-secure-systems-assets
arn:aws:sns:us-east-1:000000000000:session-events
http://localhost:4566/000000000000/analysis-jobs
http://localhost:4566/000000000000/analysis-jobs-dlq
http://localhost:4566/000000000000/analysis-results
http://localhost:4566/000000000000/analysis-results-dlq
http://localhost:4566/000000000000/session-events-gateway
http://localhost:4566/000000000000/session-events-gateway-dlq
sqs     arn:aws:sqs:us-east-1:000000000000:session-events-gateway
```

- [ ] **Step 6: Verify DLQ redrive on a primary queue**

```bash
docker exec fss-localstack awslocal sqs get-queue-attributes \
  --queue-url http://localhost:4566/000000000000/analysis-jobs \
  --attribute-names RedrivePolicy --query 'Attributes.RedrivePolicy' --output text
```

Expected (one line, JSON-encoded as a string):
```
{"deadLetterTargetArn":"arn:aws:sqs:us-east-1:000000000000:analysis-jobs-dlq","maxReceiveCount":"3"}
```

- [ ] **Step 7: Tear down and commit**

```bash
make down
cd /Users/uiradias/Repository/fiap-monorepo
git add fiap-secure-systems/docker-compose.yml \
        fiap-secure-systems/infrastructure/localstack/init/01-bootstrap.sh
git commit -m "feat(fiap-secure-systems): add localstack with S3/SNS/SQS bootstrap and DLQs"
```

---

## Task 5: OTel Collector in core compose

**Files:**
- Create: `fiap-secure-systems/infrastructure/otel/otel-collector-config.yaml`
- Modify: `fiap-secure-systems/docker-compose.yml` (add `otel-collector` service)

- [ ] **Step 1: Write the collector config**

This is the *core* config — it accepts OTLP/gRPC and OTLP/HTTP, and for now exports everything to the `debug` exporter. In Task 6 we'll add Tempo/Prometheus/Loki exporters in the observability overlay.

File: `fiap-secure-systems/infrastructure/otel/otel-collector-config.yaml`

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    send_batch_size: 1024
    timeout: 1s
  memory_limiter:
    check_interval: 1s
    limit_percentage: 75
    spike_limit_percentage: 25

exporters:
  debug:
    verbosity: basic

extensions:
  health_check:
    endpoint: 0.0.0.0:13133

service:
  extensions: [health_check]
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [debug]
    metrics:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [debug]
    logs:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [debug]
```

- [ ] **Step 2: Add the service to `docker-compose.yml`**

Append under `services:` (keeping `postgres` and `localstack`):

```yaml
  otel-collector:
    image: otel/opentelemetry-collector-contrib:0.103.0
    container_name: fss-otel-collector
    command: ["--config=/etc/otel-collector-config.yaml"]
    volumes:
      - ./infrastructure/otel/otel-collector-config.yaml:/etc/otel-collector-config.yaml:ro
    ports:
      - "4317:4317"   # OTLP/gRPC
      - "4318:4318"   # OTLP/HTTP
      - "13133:13133" # health
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost:13133/"]
      interval: 5s
      timeout: 3s
      retries: 10
      start_period: 5s
    networks: [fss]
```

- [ ] **Step 3: Bring up and verify**

```bash
cd /Users/uiradias/Repository/fiap-monorepo/fiap-secure-systems
make up
sleep 8
curl -fsS http://localhost:13133/ && echo
nc -z localhost 4317 && echo "OTLP/gRPC OK"
nc -z localhost 4318 && echo "OTLP/HTTP OK"
```

Expected:
```
{"status":"Server available","upSince":"...","uptime":"..."}
OTLP/gRPC OK
OTLP/HTTP OK
```

- [ ] **Step 4: Tear down and commit**

```bash
make down
cd /Users/uiradias/Repository/fiap-monorepo
git add fiap-secure-systems/docker-compose.yml \
        fiap-secure-systems/infrastructure/otel/otel-collector-config.yaml
git commit -m "feat(fiap-secure-systems): add OTel Collector to core compose"
```

---

## Task 6: Observability overlay (Tempo + Prometheus + Loki + Grafana)

**Files:**
- Create: `fiap-secure-systems/infrastructure/otel/tempo.yaml`
- Create: `fiap-secure-systems/infrastructure/otel/prometheus.yml`
- Create: `fiap-secure-systems/infrastructure/otel/loki.yaml`
- Create: `fiap-secure-systems/infrastructure/otel/grafana/provisioning/datasources/datasources.yaml`
- Create: `fiap-secure-systems/docker-compose.observability.yml`
- Modify: `fiap-secure-systems/infrastructure/otel/otel-collector-config.yaml` (add Tempo/Prometheus/Loki exporters as commented-out optional pipeline that activates only when those services exist; we'll switch the default pipeline to use them)

The overlay is opt-in via `make up-obs`. The OTel Collector's pipelines remain a single config; if Tempo/Prom/Loki aren't running, the OTLP/Prometheus-write/Loki-push exports retry quietly.

- [ ] **Step 1: Write `tempo.yaml`**

File: `fiap-secure-systems/infrastructure/otel/tempo.yaml`

```yaml
server:
  http_listen_port: 3200
  grpc_listen_port: 9095

distributor:
  receivers:
    otlp:
      protocols:
        grpc:
          endpoint: 0.0.0.0:4317
        http:
          endpoint: 0.0.0.0:4318

ingester:
  trace_idle_period: 10s
  max_block_bytes: 1_000_000
  max_block_duration: 5m

compactor:
  compaction:
    block_retention: 24h

storage:
  trace:
    backend: local
    local:
      path: /var/tempo/blocks
    wal:
      path: /var/tempo/wal
```

Note: Tempo listens on the same OTLP ports internally. We map the host's 4317/4318 to the OTel Collector — Tempo is reached only via the docker network from the Collector at `tempo:4317`.

- [ ] **Step 2: Write `prometheus.yml`**

File: `fiap-secure-systems/infrastructure/otel/prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: otel-collector
    static_configs:
      - targets: ["otel-collector:8889"]   # Prometheus exporter on the collector (added below)
```

- [ ] **Step 3: Write `loki.yaml`**

File: `fiap-secure-systems/infrastructure/otel/loki.yaml`

```yaml
auth_enabled: false

server:
  http_listen_port: 3100

common:
  ring:
    instance_addr: 127.0.0.1
    kvstore:
      store: inmemory
  replication_factor: 1
  path_prefix: /tmp/loki

schema_config:
  configs:
    - from: 2024-01-01
      store: tsdb
      object_store: filesystem
      schema: v13
      index:
        prefix: index_
        period: 24h

storage_config:
  filesystem:
    chunks_directory: /tmp/loki/chunks
    rules_directory: /tmp/loki/rules
  tsdb_shipper:
    active_index_directory: /tmp/loki/tsdb-active
    cache_location: /tmp/loki/tsdb-cache

limits_config:
  reject_old_samples: false
  allow_structured_metadata: true
```

- [ ] **Step 4: Write Grafana datasource provisioning**

File: `fiap-secure-systems/infrastructure/otel/grafana/provisioning/datasources/datasources.yaml`

```yaml
apiVersion: 1

datasources:
  - name: Tempo
    type: tempo
    access: proxy
    url: http://tempo:3200
    uid: tempo
    isDefault: false

  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    uid: prometheus
    isDefault: true

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    uid: loki
    isDefault: false
```

- [ ] **Step 5: Update the OTel Collector config to export to Tempo/Prom/Loki**

Replace `fiap-secure-systems/infrastructure/otel/otel-collector-config.yaml` with:

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    send_batch_size: 1024
    timeout: 1s
  memory_limiter:
    check_interval: 1s
    limit_percentage: 75
    spike_limit_percentage: 25

exporters:
  debug:
    verbosity: basic
  otlp/tempo:
    endpoint: tempo:4317
    tls:
      insecure: true
    sending_queue:
      enabled: true
    retry_on_failure:
      enabled: true
  prometheus:
    endpoint: 0.0.0.0:8889
    send_timestamps: true
    metric_expiration: 5m
  otlphttp/loki:
    endpoint: http://loki:3100/otlp
    encoding: json
    sending_queue:
      enabled: true
    retry_on_failure:
      enabled: true

extensions:
  health_check:
    endpoint: 0.0.0.0:13133

service:
  extensions: [health_check]
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [otlp/tempo, debug]
    metrics:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [prometheus, debug]
    logs:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [otlphttp/loki, debug]
```

When `make up` is used (no Tempo/Loki running), exporters retry & queue silently — telemetry is still observed via the `debug` exporter in the collector logs. With `make up-obs`, all four sinks are active.

- [ ] **Step 6: Expose port 8889 on the collector for Prometheus scraping**

Edit `fiap-secure-systems/docker-compose.yml`. In the `otel-collector` service, change the `ports:` block to:

```yaml
    ports:
      - "4317:4317"
      - "4318:4318"
      - "13133:13133"
      - "8889:8889"   # Prometheus exporter scrape target
```

- [ ] **Step 7: Write the observability overlay**

File: `fiap-secure-systems/docker-compose.observability.yml`

```yaml
services:
  tempo:
    image: grafana/tempo:2.5.0
    container_name: fss-tempo
    command: ["-config.file=/etc/tempo.yaml"]
    volumes:
      - ./infrastructure/otel/tempo.yaml:/etc/tempo.yaml:ro
    ports:
      - "3200:3200"
    networks: [fss]
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost:3200/ready"]
      interval: 5s
      timeout: 3s
      retries: 20

  prometheus:
    image: prom/prometheus:v2.51.0
    container_name: fss-prometheus
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
      - "--storage.tsdb.path=/prometheus"
      - "--storage.tsdb.retention.time=24h"
    volumes:
      - ./infrastructure/otel/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    ports:
      - "9090:9090"
    networks: [fss]
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost:9090/-/ready"]
      interval: 5s
      timeout: 3s
      retries: 20

  loki:
    image: grafana/loki:3.0.0
    container_name: fss-loki
    command: ["-config.file=/etc/loki.yaml"]
    volumes:
      - ./infrastructure/otel/loki.yaml:/etc/loki.yaml:ro
    ports:
      - "3100:3100"
    networks: [fss]
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost:3100/ready"]
      interval: 5s
      timeout: 3s
      retries: 20

  grafana:
    image: grafana/grafana:10.4.2
    container_name: fss-grafana
    environment:
      GF_AUTH_ANONYMOUS_ENABLED: "true"
      GF_AUTH_ANONYMOUS_ORG_ROLE: Admin
      GF_AUTH_DISABLE_LOGIN_FORM: "true"
    volumes:
      - ./infrastructure/otel/grafana/provisioning:/etc/grafana/provisioning:ro
    ports:
      - "3000:3000"
    networks: [fss]
    depends_on:
      tempo:
        condition: service_healthy
      prometheus:
        condition: service_healthy
      loki:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost:3000/api/health"]
      interval: 5s
      timeout: 3s
      retries: 20
```

- [ ] **Step 8: Bring up the full observability stack**

```bash
cd /Users/uiradias/Repository/fiap-monorepo/fiap-secure-systems
make nuke
make up-obs

for svc in fss-postgres fss-localstack fss-otel-collector fss-tempo fss-prometheus fss-loki fss-grafana; do
  for i in {1..60}; do
    s=$(docker inspect -f '{{.State.Health.Status}}' "$svc" 2>/dev/null || echo none)
    [ "$s" = "healthy" ] && break
    sleep 1
  done
  printf "%-22s %s\n" "$svc" "$s"
done
```

Expected: every line ends with `healthy`.

- [ ] **Step 9: Verify Grafana sees the three datasources**

```bash
sleep 3
curl -fsS http://localhost:3000/api/datasources | python3 -m json.tool | grep -E '"name"|"type"'
```

Expected: includes `"name": "Tempo"`, `"name": "Prometheus"`, `"name": "Loki"`.

- [ ] **Step 10: Tear down and commit**

```bash
make down
cd /Users/uiradias/Repository/fiap-monorepo
git add fiap-secure-systems/infrastructure/otel \
        fiap-secure-systems/docker-compose.yml \
        fiap-secure-systems/docker-compose.observability.yml
git commit -m "feat(fiap-secure-systems): add observability stack (tempo, prometheus, loki, grafana)"
```

---

## Task 7: Shared JSON-schema contracts

**Files:**
- Create: `fiap-secure-systems/infrastructure/contracts/analysis-jobs.schema.json`
- Create: `fiap-secure-systems/infrastructure/contracts/analysis-results.schema.json`
- Create: `fiap-secure-systems/infrastructure/contracts/session-events.schema.json`
- Create: `fiap-secure-systems/infrastructure/contracts/analysis-report.schema.json`

These are the single source of truth for the messaging payloads (Sections 8.4 and 7 of the spec). The application services will reference these files in their contract tests.

- [ ] **Step 1: Write `analysis-jobs.schema.json`**

File: `fiap-secure-systems/infrastructure/contracts/analysis-jobs.schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://fiap-secure-systems/contracts/analysis-jobs.schema.json",
  "title": "AnalysisJob",
  "description": "Message published by orchestrator-service to the analysis-jobs SQS queue, consumed by smart-service.",
  "type": "object",
  "additionalProperties": false,
  "required": ["schemaVersion", "jobId", "sessionId", "userId", "assets", "promptVersion", "submittedAt"],
  "properties": {
    "schemaVersion": { "type": "integer", "const": 1 },
    "jobId":        { "type": "string", "format": "uuid" },
    "sessionId":    { "type": "string", "format": "uuid" },
    "userId":       { "type": "string", "format": "uuid" },
    "assets": {
      "type": "array",
      "minItems": 1,
      "maxItems": 20,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["assetId", "s3Key", "contentType", "filename", "sizeBytes"],
        "properties": {
          "assetId":     { "type": "string", "format": "uuid" },
          "s3Key":       { "type": "string", "minLength": 1 },
          "contentType": { "type": "string", "enum": ["application/pdf", "image/png", "image/jpeg", "image/webp"] },
          "filename":    { "type": "string", "minLength": 1 },
          "sizeBytes":   { "type": "integer", "minimum": 1, "maximum": 26214400 }
        }
      }
    },
    "promptVersion": { "type": "string", "pattern": "^v[0-9]+$" },
    "submittedAt":   { "type": "string", "format": "date-time" }
  }
}
```

- [ ] **Step 2: Write `analysis-results.schema.json`**

File: `fiap-secure-systems/infrastructure/contracts/analysis-results.schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://fiap-secure-systems/contracts/analysis-results.schema.json",
  "title": "AnalysisResult",
  "description": "Message published by smart-service to the analysis-results SQS queue, consumed by orchestrator-service.",
  "type": "object",
  "additionalProperties": false,
  "required": ["schemaVersion", "jobId", "sessionId", "status", "completedAt"],
  "properties": {
    "schemaVersion": { "type": "integer", "const": 1 },
    "jobId":         { "type": "string", "format": "uuid" },
    "sessionId":     { "type": "string", "format": "uuid" },
    "status":        { "type": "string", "enum": ["STARTED", "SUCCEEDED", "FAILED"] },
    "result":        { "$ref": "analysis-report.schema.json" },
    "error": {
      "type": "object",
      "additionalProperties": false,
      "required": ["code", "message"],
      "properties": {
        "code":    { "type": "string", "minLength": 1 },
        "message": { "type": "string", "minLength": 1 }
      }
    },
    "modelMetadata": {
      "type": "object",
      "additionalProperties": false,
      "required": ["model"],
      "properties": {
        "model":      { "type": "string", "minLength": 1 },
        "tokensIn":   { "type": "integer", "minimum": 0 },
        "tokensOut":  { "type": "integer", "minimum": 0 },
        "durationMs": { "type": "integer", "minimum": 0 }
      }
    },
    "completedAt": { "type": "string", "format": "date-time" }
  },
  "allOf": [
    {
      "if":   { "properties": { "status": { "const": "SUCCEEDED" } } },
      "then": { "required": ["result", "modelMetadata"] }
    },
    {
      "if":   { "properties": { "status": { "const": "FAILED" } } },
      "then": { "required": ["error"] }
    }
  ]
}
```

- [ ] **Step 3: Write `session-events.schema.json`**

File: `fiap-secure-systems/infrastructure/contracts/session-events.schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://fiap-secure-systems/contracts/session-events.schema.json",
  "title": "SessionEvent",
  "description": "Message published by orchestrator-service to the session-events SNS topic and fanned out to per-gateway SQS queues.",
  "type": "object",
  "additionalProperties": false,
  "required": ["schemaVersion", "eventId", "sessionId", "userId", "toState", "occurredAt"],
  "properties": {
    "schemaVersion": { "type": "integer", "const": 1 },
    "eventId":   { "type": "string", "format": "uuid" },
    "sessionId": { "type": "string", "format": "uuid" },
    "userId":    { "type": "string", "format": "uuid" },
    "fromState": {
      "type": ["string", "null"],
      "enum": [
        null,
        "CREATED",
        "ASSETS_UPLOADED",
        "QUEUED_FOR_ANALYSIS",
        "ANALYZING",
        "ANALYSIS_COMPLETED",
        "REPORT_READY",
        "FAILED",
        "CANCELED"
      ]
    },
    "toState": {
      "type": "string",
      "enum": [
        "CREATED",
        "ASSETS_UPLOADED",
        "QUEUED_FOR_ANALYSIS",
        "ANALYZING",
        "ANALYSIS_COMPLETED",
        "REPORT_READY",
        "FAILED",
        "CANCELED"
      ]
    },
    "payload":   { "type": "object" },
    "occurredAt": { "type": "string", "format": "date-time" }
  }
}
```

- [ ] **Step 4: Write `analysis-report.schema.json`**

This is the AI output schema (spec Section 7) — the persisted shape and the value of `result` inside `analysis-results.schema.json`.

File: `fiap-secure-systems/infrastructure/contracts/analysis-report.schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://fiap-secure-systems/contracts/analysis-report.schema.json",
  "title": "AnalysisReport",
  "description": "Structured architecture-review output produced by smart-service.",
  "type": "object",
  "additionalProperties": false,
  "required": ["summary", "components", "risks", "improvements", "strengths", "confidence", "model_metadata"],
  "properties": {
    "summary":    { "type": "string", "minLength": 1, "maxLength": 1000 },
    "confidence": { "type": "string", "enum": ["high", "medium", "low"] },
    "components": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["name", "kind", "responsibility", "relevance", "evidence"],
        "properties": {
          "name":           { "type": "string", "minLength": 1 },
          "kind":           { "type": "string", "enum": ["service", "datastore", "queue", "gateway", "client", "external", "other"] },
          "responsibility": { "type": "string", "minLength": 1 },
          "relevance":      { "type": "string", "enum": ["high", "medium", "low"] },
          "evidence":       { "type": "string", "minLength": 1 }
        }
      }
    },
    "risks": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["title", "category", "severity", "description", "affected_components", "recommendation"],
        "properties": {
          "title":               { "type": "string", "minLength": 1 },
          "category":            { "type": "string", "enum": ["security", "scalability", "availability", "cost", "operability", "data", "compliance"] },
          "severity":            { "type": "string", "enum": ["critical", "high", "medium", "low"] },
          "description":         { "type": "string", "minLength": 1 },
          "affected_components": { "type": "array", "items": { "type": "string" } },
          "recommendation":      { "type": "string", "minLength": 1 }
        }
      }
    },
    "improvements": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["title", "rationale", "impact", "effort", "affected_components"],
        "properties": {
          "title":               { "type": "string", "minLength": 1 },
          "rationale":           { "type": "string", "minLength": 1 },
          "impact":              { "type": "string", "enum": ["high", "medium", "low"] },
          "effort":              { "type": "string", "enum": ["high", "medium", "low"] },
          "affected_components": { "type": "array", "items": { "type": "string" } }
        }
      }
    },
    "strengths": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["title", "description"],
        "properties": {
          "title":       { "type": "string", "minLength": 1 },
          "description": { "type": "string", "minLength": 1 }
        }
      }
    },
    "model_metadata": {
      "type": "object",
      "additionalProperties": false,
      "required": ["model"],
      "properties": {
        "model":       { "type": "string", "minLength": 1 },
        "tokens_in":   { "type": "integer", "minimum": 0 },
        "tokens_out":  { "type": "integer", "minimum": 0 },
        "duration_ms": { "type": "integer", "minimum": 0 }
      }
    }
  }
}
```

- [ ] **Step 5: Validate every schema is parseable JSON Schema draft-07**

```bash
cd /Users/uiradias/Repository/fiap-monorepo/fiap-secure-systems
python3 - <<'PY'
import json, sys, glob
try:
    import jsonschema
except ImportError:
    sys.exit("install: pip install jsonschema")
from jsonschema import Draft7Validator

ok = True
for f in sorted(glob.glob("infrastructure/contracts/*.schema.json")):
    with open(f) as fh:
        schema = json.load(fh)
    try:
        Draft7Validator.check_schema(schema)
        print(f"OK   {f}")
    except Exception as e:
        ok = False
        print(f"FAIL {f}: {e}")
sys.exit(0 if ok else 1)
PY
```

Expected: four `OK` lines, exit 0. (If `jsonschema` is missing: `pip install jsonschema` first or use `pipx run --spec jsonschema python3 -c '...'`.)

- [ ] **Step 6: Commit**

```bash
cd /Users/uiradias/Repository/fiap-monorepo
git add fiap-secure-systems/infrastructure/contracts/
git commit -m "feat(fiap-secure-systems): add JSON-schema contracts for messaging and analysis report"
```

---

## Task 8: Stack smoke test

**Files:**
- Create: `fiap-secure-systems/infrastructure/smoke/check-stack.sh`
- Modify: `fiap-secure-systems/Makefile` (replace the `smoke` placeholder)

- [ ] **Step 1: Write the smoke script**

File: `fiap-secure-systems/infrastructure/smoke/check-stack.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

PASS=0
FAIL=0

check () {
  local label="$1" cmd="$2" expect="$3"
  local out
  if out=$(eval "$cmd" 2>&1); then
    if echo "$out" | grep -q "$expect"; then
      printf "  \033[32mOK\033[0m   %s\n" "$label"
      PASS=$((PASS+1))
      return 0
    fi
  fi
  printf "  \033[31mFAIL\033[0m %s  (got: %s)\n" "$label" "$(echo "$out" | head -c 200)"
  FAIL=$((FAIL+1))
}

echo "== Postgres =="
for db in gateway_db orchestrator_db smart_db; do
  check "$db exists" \
    "docker exec fss-postgres psql -U postgres -tAc \"SELECT 1 FROM pg_database WHERE datname='$db'\"" \
    "1"
done

echo "== LocalStack: S3 =="
check "bucket fiap-secure-systems-assets" \
  "docker exec fss-localstack awslocal s3api list-buckets --query 'Buckets[].Name' --output text" \
  "fiap-secure-systems-assets"

echo "== LocalStack: SNS =="
check "topic session-events" \
  "docker exec fss-localstack awslocal sns list-topics --query 'Topics[].TopicArn' --output text" \
  ":session-events"

echo "== LocalStack: SQS =="
for q in analysis-jobs analysis-jobs-dlq \
         analysis-results analysis-results-dlq \
         session-events-gateway session-events-gateway-dlq; do
  check "queue $q" \
    "docker exec fss-localstack awslocal sqs list-queues --query 'QueueUrls[]' --output text" \
    "/$q"
done

echo "== LocalStack: subscription =="
check "session-events → session-events-gateway" \
  "docker exec fss-localstack awslocal sns list-subscriptions --query 'Subscriptions[].Endpoint' --output text" \
  ":session-events-gateway"

echo "== OTel Collector =="
check "health" \
  "curl -fsS http://localhost:13133/" \
  "Server available"

echo
printf "PASS=%d FAIL=%d\n" "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
```

- [ ] **Step 2: Make it executable**

```bash
cd /Users/uiradias/Repository/fiap-monorepo/fiap-secure-systems
chmod +x infrastructure/smoke/check-stack.sh
```

- [ ] **Step 3: Replace the `smoke` target in the Makefile**

Edit `fiap-secure-systems/Makefile`. Replace the `smoke` target's body with:

```makefile
.PHONY: smoke
smoke: ## Verify the running infrastructure stack
	@./infrastructure/smoke/check-stack.sh
```

- [ ] **Step 4: Bring the core stack up and run smoke**

```bash
cd /Users/uiradias/Repository/fiap-monorepo/fiap-secure-systems
make nuke
make up

# wait for everything healthy
for svc in fss-postgres fss-localstack fss-otel-collector; do
  for i in {1..60}; do
    s=$(docker inspect -f '{{.State.Health.Status}}' "$svc" 2>/dev/null || echo none)
    [ "$s" = "healthy" ] && break
    sleep 1
  done
done

make smoke
```

Expected: every check prints `OK`, final line `PASS=13 FAIL=0`, exit 0.

- [ ] **Step 5: Tear down and commit**

```bash
make down
cd /Users/uiradias/Repository/fiap-monorepo
git add fiap-secure-systems/Makefile \
        fiap-secure-systems/infrastructure/smoke/check-stack.sh
git commit -m "feat(fiap-secure-systems): add stack smoke test"
```

---

## Task 9: Root README quickstart

**Files:**
- Create: `fiap-secure-systems/README.md`

- [ ] **Step 1: Write the README**

File: `fiap-secure-systems/README.md`

````markdown
# fiap-secure-systems

A distributed system that ingests system-architecture diagrams (PDF/image), persists them in S3 under a single identifier, and uses an AI model to produce a structured architecture review (relevant components, risks, improvements, strengths).

## Status

Foundation in place. Application services are implemented across subsequent sub-plans.

- See [`docs/superpowers/specs/2026-05-05-fiap-secure-systems-design.md`](docs/superpowers/specs/2026-05-05-fiap-secure-systems-design.md) for the full design.
- See [`docs/superpowers/plans/`](docs/superpowers/plans/) for the implementation plans.

## Architecture (one-liner)

`gateway-service` (Spring Boot, public, JWT) → `orchestrator-service` (Spring Boot, internal, owns session state) ↔ SQS ↔ `smart-service` (FastAPI, internal, calls Anthropic Claude). Postgres database-per-service; SNS+SQS fan-out for session events; WebSocket from gateway to client.

## Quickstart

Prerequisites: Docker (with Compose v2), `curl`, `nc`. (Python 3 + `jsonschema` is only needed if you re-validate the JSON schemas under `infrastructure/contracts/`.)

```bash
cp .env.example .env             # one-time
make up                          # core infra: postgres + localstack + otel-collector
make smoke                       # verify everything provisioned
make up-obs                      # add tempo + prometheus + loki + grafana on top
open http://localhost:3000       # Grafana (anonymous admin)
make down                        # stop containers (volumes preserved)
make nuke                        # stop + delete volumes
```

## What this repo contains today

| Path | Purpose |
|---|---|
| `docker-compose.yml` | Core infra (Postgres, LocalStack, OTel Collector) |
| `docker-compose.observability.yml` | Tempo + Prometheus + Loki + Grafana overlay |
| `infrastructure/postgres/init/` | Bootstraps `gateway_db`, `orchestrator_db`, `smart_db` |
| `infrastructure/localstack/init/` | Bootstraps S3 bucket, SNS topic, SQS queues + DLQs, subscription |
| `infrastructure/otel/` | Collector, Tempo, Prometheus, Loki, Grafana configs |
| `infrastructure/contracts/` | JSON Schemas for messaging payloads + AI report |
| `infrastructure/smoke/check-stack.sh` | Verifies the running stack |
| `Makefile` | Top-level commands |
| `.env.example` | Template environment variables |

## Resources provisioned by `make up`

- **Postgres** at `localhost:5432` with three logical DBs (`gateway_db`, `orchestrator_db`, `smart_db`)
- **LocalStack** at `localhost:4566` — S3 bucket `fiap-secure-systems-assets`, SNS topic `session-events`, SQS queues `analysis-jobs`, `analysis-results`, `session-events-gateway` (each with a DLQ; redrive after 3 receives)
- **OTel Collector** receiving OTLP/gRPC on `localhost:4317`, OTLP/HTTP on `localhost:4318`, Prometheus exporter on `localhost:8889`, health on `localhost:13133`

## Resources added by `make up-obs`

- **Tempo** UI/API at `localhost:3200`
- **Prometheus** at `localhost:9090` (scrapes the OTel Collector's Prometheus exporter)
- **Loki** at `localhost:3100`
- **Grafana** at `localhost:3000` (anonymous admin; Tempo/Prometheus/Loki provisioned as datasources)

## License

(Internal academic project — license TBD.)
````

- [ ] **Step 2: Verify the README renders without errors**

```bash
cd /Users/uiradias/Repository/fiap-monorepo/fiap-secure-systems
[ -s README.md ] && echo "README written ($(wc -l < README.md) lines)"
```

Expected: `README written (NN lines)` where `NN` ≈ 60.

- [ ] **Step 3: Commit**

```bash
cd /Users/uiradias/Repository/fiap-monorepo
git add fiap-secure-systems/README.md
git commit -m "docs(fiap-secure-systems): add root README with quickstart"
```

---

## Final verification (after all 9 tasks)

Run from a clean state to confirm the foundation is reproducible:

```bash
cd /Users/uiradias/Repository/fiap-monorepo/fiap-secure-systems
make nuke
make up

# wait for health
for svc in fss-postgres fss-localstack fss-otel-collector; do
  for i in {1..60}; do
    s=$(docker inspect -f '{{.State.Health.Status}}' "$svc" 2>/dev/null || echo none)
    [ "$s" = "healthy" ] && break
    sleep 1
  done
done

make smoke
make up-obs

# wait again for the obs services
for svc in fss-tempo fss-prometheus fss-loki fss-grafana; do
  for i in {1..60}; do
    s=$(docker inspect -f '{{.State.Health.Status}}' "$svc" 2>/dev/null || echo none)
    [ "$s" = "healthy" ] && break
    sleep 1
  done
done

curl -fsS http://localhost:3000/api/health | grep -q '"database":"ok"' && echo "Grafana OK"
curl -fsS http://localhost:9090/-/ready  | grep -q "Ready"           && echo "Prometheus OK"
curl -fsS http://localhost:3100/ready    | grep -q "ready"           && echo "Loki OK"
curl -fsS http://localhost:3200/ready    | grep -q "ready"           && echo "Tempo OK"

make down
```

All four observability checks should print `OK`. `make smoke` exits 0 with `PASS=13 FAIL=0`.

---

## What unlocks next

With this plan merged, sub-plans 2–4 (smart-service, orchestrator-service, gateway-service) can develop in parallel against:
- A live Postgres with their own DB and credentials.
- A live LocalStack with the bucket, topic, queues, and DLQs they expect.
- A live OTel Collector ready to receive OTLP traces/metrics/logs.
- Authoritative JSON Schemas in `infrastructure/contracts/` to wire into contract tests.

The next plan (sub-plan 2 — smart-service) will be authored after this foundation is committed.
