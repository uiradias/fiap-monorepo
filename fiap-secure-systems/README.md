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

```mermaid
flowchart TB
    User(["End user<br/>(browser)"])

    subgraph Apps["Application services"]
        Front["React + Vite SPA<br/>:5173 → :80 nginx"]
        GW["gateway-service<br/>:8080  Spring Boot 3.4 / Java 21<br/>JWT RS256, multipart upload,<br/>internal HMAC signer,<br/>WebSocket broadcaster"]
        Orch["orchestrator-service<br/>:8081  Spring Boot 3.4 / Java 21<br/>SessionStateMachine, outbox + relay,<br/>internal REST + HMAC filter,<br/>analysis-result consumer"]
        Smart["smart-service<br/>:8000  Python 3.12 / FastAPI<br/>baseline (Sonnet) + grounded (RAG)<br/>see smart-service/README.md"]
    end

    subgraph Data["Shared data plane"]
        PG[("postgres :5432<br/>gateway_db / orchestrator_db /<br/>smart_db (+ pgvector)")]
        LS[("localstack :4566<br/>S3 / SNS / SQS / DLQs")]
    end

    subgraph Ext["External AI providers (smart-service only)"]
        Claude[("Anthropic<br/>Sonnet 4.6 + Haiku 4.5")]
        Voyage[("Voyage AI<br/>voyage-3 embeddings")]
    end

    User -->|HTTPS| Front
    Front -->|REST + WebSocket| GW
    GW -->|"REST (HMAC)"| Orch
    GW -.->|session-events SQS poller| GW
    Orch -->|analysis-jobs SQS| Smart
    Smart -->|analysis-results SQS| Orch
    Orch -->|"session-events SNS to SQS"| GW

    GW --- PG
    Orch --- PG
    Smart --- PG
    GW --- LS
    Orch --- LS
    Smart --- LS

    Smart -.->|when grounded| Voyage
    Smart -.-> Claude

    classDef store fill:#e8f4f8,stroke:#0c5460
    classDef ext fill:#fff3cd,stroke:#856404
    classDef app fill:#e8f5e9,stroke:#1b5e20
    class PG,LS store
    class Claude,Voyage ext
    class Front,GW,Orch,Smart app
```

The smart-service module supports two interchangeable analysis pipelines
selected at boot via `SMART_ANALYSIS_STRATEGY`:

- **`baseline`** (default): single Sonnet 4.6 call with prompt-engineered JSON.
- **`grounded`**: four-stage RAG (Haiku vision extraction → canonicalisation →
  pgvector retrieval against a curated 30-pattern corpus → Sonnet tool-use
  emission with hallucination filter).

The two paths share the same `analysis-report.schema.json` and SQS envelope;
the optional `citations` field is populated on grounded outputs only. See
[`smart-service/README.md`](smart-service/README.md) for diagrams and details.

## AI/ML deliverable requirements

The project's AI/ML requirements (specified in Portuguese) — *detecção de
componentes em imagens, classificação de riscos, LLM com guardrails, prompt
engineering com avaliação de consistência*, plus the four minimum requirements
(*pipeline claro*, *justificativa*, *demonstração prática*, *discussão de
limitações*) — are cross-referenced to the implementing code in
[`smart-service/README.md` → "AI/ML requirements coverage"](smart-service/README.md#aiml-requirements-coverage).
Known limitations are consolidated in
[`smart-service/README.md` → "Known limitations"](smart-service/README.md#known-limitations).

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md).
