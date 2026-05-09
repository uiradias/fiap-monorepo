# fiap-secure-systems

Distributed system for AI-assisted architecture review. Three Spring Boot / Python services + a React SPA, all runnable via docker-compose.

## Status

| | |
|---|---|
| ci-smart       | ![ci-smart](https://github.com/uiradias/fiap-monorepo/actions/workflows/ci-smart.yml/badge.svg)             |
| ci-orchestrator| ![ci-orchestrator](https://github.com/uiradias/fiap-monorepo/actions/workflows/ci-orchestrator.yml/badge.svg) |
| ci-gateway     | ![ci-gateway](https://github.com/uiradias/fiap-monorepo/actions/workflows/ci-gateway.yml/badge.svg)         |
| ci-frontend    | ![ci-frontend](https://github.com/uiradias/fiap-monorepo/actions/workflows/ci-frontend.yml/badge.svg)       |
| e2e            | ![e2e](https://github.com/uiradias/fiap-monorepo/actions/workflows/e2e.yml/badge.svg)                       |

## Quick start

```bash
make gen-jwt-keys       # generate RS256 keypair for gateway-service (gitignored)
make up                 # postgres + localstack + otel-collector
make smart-up           # add smart-service
make orch-up            # add orchestrator-service
make gw-up              # add gateway-service
make front-up           # add frontend (nginx)

make smoke              # PASS=19/0
make front-round-trip   # full SPA register → finalize → REPORT_READY
```

Browse the SPA at <http://localhost:5173>.

## Observability

```bash
make up-obs             # adds Tempo + Loki + Prometheus + Grafana
```

- Grafana: <http://localhost:3000> (anonymous admin) — five dashboards under "fiap-secure-systems":
  - `smart-service`, `orchestrator-service`, `gateway-service`, `frontend`, `session-lifecycle`
- Prometheus: <http://localhost:9090>
- Tempo: <http://localhost:3200>
- Loki: <http://localhost:3100>

## Architecture

See [`docs/superpowers/specs/2026-05-05-fiap-secure-systems-design.md`](docs/superpowers/specs/2026-05-05-fiap-secure-systems-design.md) for the design doc; sub-plans land under [`docs/superpowers/plans/`](docs/superpowers/plans/).

```
                         ┌─────────────────────┐
                         │   React + Vite SPA  │   :5173 (host) → :80 (nginx)
                         └──────────┬──────────┘
                            REST + WebSocket
                                    │
                          ┌─────────▼─────────┐
                          │  gateway-service  │   :8080  Spring Boot 3.4 / Java 21
                          └────┬───────┬──────┘   - JWT (RS256) + bcrypt
                               │       ▲
                       REST    │       │  consumes session-events SQS
                               │       │
                          ┌────▼───────┴──────┐
                          │ orchestrator-svc  │   :8081  Spring Boot 3.4 / Java 21
                          └────┬──────────────┘   - SessionStateMachine + outbox + OutboxRelay
                               │
                          analysis-jobs SQS
                               ▼
                          ┌────────────────────┐
                          │   smart-service    │   :8000  Python 3.12 / FastAPI
                          └────────────────────┘   - Anthropic Claude (with prompt caching)

  postgres :5432  (gateway_db / orchestrator_db / smart_db)
  localstack :4566 (S3 / SNS / SQS)
```

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md).
