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
