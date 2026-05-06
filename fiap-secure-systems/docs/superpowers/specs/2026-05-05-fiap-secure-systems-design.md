# fiap-secure-systems — Design

**Date:** 2026-05-05
**Status:** Approved (pending user review of this document)
**Target:** Production-grade distributed system for AI-assisted architecture review

---

## 1. Purpose

A distributed system that ingests system-architecture design assets (PDFs and images), persists them under a single unique identifier, and uses an AI model to produce a structured review identifying relevant components, risks, improvements, and strengths. The system is delivered as three independently deployable services plus a minimal demo frontend, all runnable locally via docker-compose.

## 2. Goals & non-goals

### Goals
- Three deployable services with hexagonal architecture: `gateway-service` (public), `orchestrator-service` (internal), `smart-service` (internal, AI-facing).
- A minimal React + Vite frontend that exercises the full upload → analyze → report flow over HTTP and WebSocket.
- Real-time session lifecycle feedback to the client over WebSocket, sourced from an SNS+SQS fan-out.
- Structured AI output with a fixed JSON schema persisted in the orchestrator and queryable by `sessionId`.
- Database-per-service via three logical Postgres databases.
- Production-grade quality bar: JWT auth, RFC 7807 errors, optimistic locking, transactional outbox, retries with backoff, DLQs, replay endpoints, OpenTelemetry tracing/metrics/logs, Micrometer (JVM), structlog (Python), Testcontainers integration tests, Pact contract tests, Playwright e2e, GitHub Actions CI.
- Entire stack runnable offline via docker-compose + LocalStack.

### Non-goals
- Multi-tenant isolation beyond per-user session ownership.
- Streaming AI responses.
- File deduplication, thumbnail generation, asset preview.
- Admin UI (admin operations are CLI/HTTP only).
- Production secret-manager integration (env placeholders only).

## 3. Decisions log

| # | Decision | Choice |
|---|---|---|
| 1 | Quality target | Full production-grade |
| 2 | Inter-service comms | Async via SQS (LocalStack); WebSocket to client |
| 3 | AI provider | Anthropic Claude Sonnet 4.6 via Anthropic SDK, swappable via port |
| 4 | Persistence model | Database-per-service, one Postgres container, three logical DBs |
| 5 | Authentication | JWT (RS256) issued by gateway; internal HMAC for service-to-service |
| 6 | Frontend scope | Minimal React + Vite demo (upload + session WS view) |
| 7 | Session state machine | `CREATED → ASSETS_UPLOADED → QUEUED_FOR_ANALYSIS → ANALYZING → ANALYSIS_COMPLETED → REPORT_READY` (+ `FAILED`, `CANCELED`) |
| 8 | AI output schema | Fixed JSON: summary, components[], risks[], improvements[], strengths[], confidence, model_metadata |
| 9 | WS event sourcing | Orchestrator → SNS → per-gateway SQS fan-out |
| 10 | JDK / Spring Boot | Java 21 / Spring Boot 3.4.x |
| 11 | Build tool | Gradle (Kotlin DSL) |
| 12 | Python framework | FastAPI + Uvicorn (Python 3.12), `uv` + `pyproject.toml` |
| 13 | Migrations | Flyway (Spring), Alembic (Python) |
| 14 | Observability | Micrometer Observation + OTel bridge → OTLP → Collector → Tempo + Prometheus + Loki + Grafana |
| 15 | Upload limits | ≤ 20 files/session, ≤ 25 MB/file, types: `application/pdf`, `image/png`, `image/jpeg`, `image/webp` |
| 16 | CI | GitHub Actions; per-service workflows + e2e workflow |

## 4. System topology

```
                       ┌──────────────────────┐
                       │   React + Vite SPA   │
                       │   (frontend, :5173)  │
                       └──────────┬───────────┘
                          REST + WebSocket
                                  │
                        ┌─────────▼──────────┐
                        │  gateway-service   │  Spring Boot 3.4 / Java 21
                        │  :8080 (public)    │  - JWT auth
                        │                    │  - Public REST (uploads, sessions)
                        │                    │  - WebSocket /ws/sessions/{id}
                        │                    │  - S3 direct upload
                        │                    │  - DB: gateway_db
                        └────┬───────┬───────┘
                             │       ▲
                  REST       │       │  consumes session-events SQS (per-replica)
                  (internal) │       │
                             │       │  publishes ▲
                        ┌────▼───────┴───────┐
                        │ orchestrator-svc   │  Spring Boot 3.4 / Java 21
                        │ :8081 (internal)   │  - Session state machine
                        │                    │  - SNS publisher (session-events)
                        │                    │  - SQS publisher (analysis-jobs)
                        │                    │  - DB: orchestrator_db
                        └────┬───────────────┘
                             │  produces analysis-jobs SQS
                             ▼
                        ┌────────────────────┐
                        │   smart-service    │  Python 3.12 / FastAPI
                        │   :8000 (internal) │  - SQS consumer (jobs)
                        │                    │  - Anthropic Claude SDK
                        │                    │  - S3 reader for assets
                        │                    │  - DB: smart_db (audit/results)
                        └────────────────────┘

  Shared infra (compose):
    postgres :5432   (3 logical DBs)
    localstack :4566 (S3, SNS, SQS)
    otel-collector + tempo + prometheus + loki + grafana :3000
```

The gateway is the only public surface. Orchestrator and smart-service bind to the internal docker network. Two SQS topics matter: `analysis-jobs` (orchestrator → smart) and `session-events` (orchestrator → SNS → fanout → per-gateway SQS). DLQs are paired with each work queue.

## 5. Service internals (hexagonal)

Each service follows the same shape: **domain** is pure (no framework imports), **application** orchestrates use cases, **adapters** speak to the outside world. Spring/FastAPI annotations live only in adapters and configuration.

### 5.1 gateway-service

```
gateway-service/
├── build.gradle.kts
└── src/main/java/com/fiap/gateway/
    ├── GatewayApplication.java
    ├── domain/
    │   ├── model/                       # AssetBundle, Asset, Session, User, …
    │   ├── port/in/                     # UploadAssetsUseCase, GetSessionUseCase,
    │   │                                #   AuthenticateUseCase, StreamSessionEventsUseCase
    │   └── port/out/                    # AssetStoragePort, SessionRegistryPort,
    │                                    #   UserRepositoryPort, OrchestratorClientPort,
    │                                    #   SessionEventSourcePort, TokenIssuerPort
    ├── application/
    │   └── service/                     # one per use case
    ├── adapter/in/
    │   ├── rest/                        # AssetsController, SessionsController,
    │   │                                #   AuthController, GlobalExceptionHandler
    │   ├── websocket/                   # SessionEventsWsHandler, WebSocketConfig
    │   └── dto/                         # request/response records
    ├── adapter/out/
    │   ├── persistence/                 # JPA entities, repositories, port impls
    │   ├── s3/                          # S3AssetStorageAdapter (AWS SDK v2)
    │   ├── messaging/                   # SqsSessionEventConsumer
    │   ├── http/                        # OrchestratorRestClient (WebClient
    │   │                                #   with InternalHmacRequestSigner interceptor)
    │   └── security/                    # JwtTokenIssuer, JwtAuthenticationFilter,
    │                                    #   InternalHmacRequestSigner
    ├── config/
    └── infrastructure/observability/
```

### 5.2 orchestrator-service

```
orchestrator-service/
└── src/main/java/com/fiap/orchestrator/
    ├── OrchestratorApplication.java
    ├── domain/
    │   ├── model/                       # Session, SessionState, SessionEvent,
    │   │                                #   AnalysisJob, AnalysisReport
    │   ├── stateMachine/SessionStateMachine.java
    │   ├── port/in/                     # CreateSessionUseCase, RecordAssetsUploadedUseCase,
    │   │                                #   EnqueueAnalysisUseCase, HandleAnalysisCompletedUseCase,
    │   │                                #   CancelSessionUseCase, GetSessionUseCase
    │   └── port/out/                    # SessionRepositoryPort, ReportRepositoryPort,
    │                                    #   AnalysisJobPublisherPort, SessionEventPublisherPort
    ├── application/service/             # emits SessionEvent on every transition
    ├── adapter/in/
    │   ├── rest/                        # internal-only controllers
    │   ├── messaging/                   # AnalysisResultSqsConsumer
    │   └── security/                    # InternalHmacFilter (validates inbound HMAC)
    ├── adapter/out/
    │   ├── persistence/                 # Flyway migrations, entities, repositories
    │   └── messaging/                   # SqsAnalysisJobPublisher, SnsSessionEventPublisher,
    │                                    #   OutboxRelay (drains outbox_messages to SNS or SQS by event_type)
    ├── config/
    └── infrastructure/observability/
```

### 5.3 smart-service

```
smart-service/
├── pyproject.toml
└── smart_service/
    ├── main.py                          # FastAPI app + worker bootstrap
    ├── domain/
    │   ├── model.py                     # AnalysisJob, AnalysisResult, Component, Risk, …
    │   └── ports.py                     # typed Protocols for ports
    ├── application/
    │   └── analyze_assets_service.py
    ├── adapter/
    │   ├── inbound/
    │   │   ├── rest.py                  # /health, /readiness, /admin/replay
    │   │   └── sqs_consumer.py          # long-polling worker
    │   ├── outbound/
    │   │   ├── s3_asset_reader.py
    │   │   ├── claude_model_adapter.py  # anthropic SDK + prompt caching
    │   │   ├── sqs_result_publisher.py
    │   │   └── postgres_audit_repository.py
    │   └── schema/                      # Pydantic schemas
    ├── config/
    │   ├── settings.py                  # pydantic-settings
    │   └── wiring.py                    # composition root
    ├── infrastructure/
    │   ├── observability.py
    │   └── alembic/
    └── tests/
```

### 5.4 Hexagonal invariants

- `domain/` has zero framework imports (no Spring, no FastAPI, no SQLAlchemy, no AWS SDK).
- Ports are interfaces in `domain/port/`; implementations live in `adapter/out/`.
- Composition lives only in `config/`.
- Python uses `Protocol` types instead of abstract base classes for ports.

## 6. Data model

All IDs are UUID v4. All timestamps are `TIMESTAMPTZ`. `bundleId == sessionId == report.session_id` end-to-end.

### 6.1 gateway_db

```sql
users (
  id UUID PK,
  email CITEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,             -- bcrypt cost 12
  display_name TEXT,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);

refresh_tokens (
  id UUID PK,
  user_id UUID FK→users NOT NULL,
  token_hash TEXT NOT NULL,                 -- sha256 of opaque token
  expires_at TIMESTAMPTZ NOT NULL,
  revoked_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL
);

asset_bundles (
  id UUID PK,                               -- the public unique identifier
  user_id UUID FK→users NOT NULL,
  status TEXT NOT NULL,                     -- INITIATED|UPLOADING|UPLOADED|FAILED
  asset_count INT NOT NULL,
  total_bytes BIGINT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);

assets (
  id UUID PK,
  bundle_id UUID FK→asset_bundles NOT NULL,
  s3_key TEXT NOT NULL,
  filename TEXT NOT NULL,
  content_type TEXT NOT NULL,
  size_bytes BIGINT NOT NULL,
  checksum_sha256 TEXT NOT NULL,
  uploaded_at TIMESTAMPTZ NOT NULL,
  UNIQUE(bundle_id, s3_key)
);

session_projections (                       -- current-state mirror
  id UUID PK,                               -- equal to bundle_id
  state TEXT NOT NULL,
  last_event_at TIMESTAMPTZ NOT NULL,
  failure_reason TEXT,
  report_id UUID
);

session_event_log (                         -- full event history; source of WS replay AND SQS dedup
  event_id UUID PK,                         -- doubles as dedup key (PK conflict on duplicate)
  session_id UUID NOT NULL,
  from_state TEXT,
  to_state TEXT NOT NULL,
  payload JSONB NOT NULL DEFAULT '{}',
  occurred_at TIMESTAMPTZ NOT NULL,
  received_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX session_event_log_by_session ON session_event_log (session_id, occurred_at);
```

### 6.2 orchestrator_db

```sql
sessions (
  id UUID PK,
  user_id UUID NOT NULL,
  state TEXT NOT NULL,
  asset_count INT NOT NULL,
  failure_reason TEXT,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL,
  version BIGINT NOT NULL DEFAULT 0          -- optimistic lock
);

session_events (                              -- append-only
  id UUID PK,
  session_id UUID FK→sessions NOT NULL,
  from_state TEXT,
  to_state TEXT NOT NULL,
  payload JSONB NOT NULL DEFAULT '{}',
  occurred_at TIMESTAMPTZ NOT NULL,
  published_at TIMESTAMPTZ                    -- null until SNS publish succeeded
);

outbox_messages (                             -- transactional outbox; one table for both destinations
  id UUID PK,
  aggregate_id UUID NOT NULL,                 -- session_id
  destination TEXT NOT NULL,                  -- 'SNS:session-events' | 'SQS:analysis-jobs'
  event_type TEXT NOT NULL,                   -- 'SessionStateChanged' | 'AnalysisJobRequested'
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  published_at TIMESTAMPTZ,                   -- null until OutboxRelay confirms publish
  attempts INT NOT NULL DEFAULT 0,
  last_error TEXT
);
CREATE INDEX outbox_unpublished ON outbox_messages (created_at) WHERE published_at IS NULL;

analysis_reports (                            -- the persisted Q8 schema
  id UUID PK,
  session_id UUID FK→sessions UNIQUE NOT NULL,
  summary TEXT NOT NULL,
  confidence TEXT NOT NULL,
  payload JSONB NOT NULL,
  model_metadata JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL
);

processed_jobs (                              -- inbound SQS dedup
  job_id UUID PK,
  processed_at TIMESTAMPTZ NOT NULL
);
```

### 6.3 smart_db

```sql
analysis_runs (
  id UUID PK,
  session_id UUID NOT NULL,
  job_id UUID UNIQUE NOT NULL,
  status TEXT NOT NULL,                       -- RUNNING|SUCCEEDED|FAILED
  asset_keys JSONB NOT NULL,
  prompt_version TEXT NOT NULL,
  model TEXT NOT NULL,
  tokens_in INT,
  tokens_out INT,
  duration_ms INT,
  error TEXT,
  result JSONB,
  started_at TIMESTAMPTZ NOT NULL,
  finished_at TIMESTAMPTZ
);

processed_jobs (
  job_id UUID PK,
  processed_at TIMESTAMPTZ NOT NULL
);
```

### 6.4 Cross-cutting persistence rules
- **Transactional outbox** in orchestrator: state transitions and outbound messages written in one transaction; `OutboxRelay` publishes to SNS or SQS (per `destination`), marking `published_at` only on confirmation.
- **Inbound dedup** in every consumer: gateway uses `session_event_log` PK conflict on `event_id`; orchestrator and smart-service use `processed_jobs` PK conflict on `job_id`. Duplicates are silently ack'd.
- **Optimistic locking** on `sessions.version` (JPA `@Version`); on conflict, re-read and retry once before failing.

## 7. AI output schema (`analysis_reports.payload`)

```json
{
  "summary": "string — 2-3 sentence executive summary",
  "components": [
    {
      "name": "string",
      "kind": "service|datastore|queue|gateway|client|external|other",
      "responsibility": "string",
      "relevance": "high|medium|low",
      "evidence": "string"
    }
  ],
  "risks": [
    {
      "title": "string",
      "category": "security|scalability|availability|cost|operability|data|compliance",
      "severity": "critical|high|medium|low",
      "description": "string",
      "affected_components": ["componentName"],
      "recommendation": "string"
    }
  ],
  "improvements": [
    {
      "title": "string",
      "rationale": "string",
      "impact": "high|medium|low",
      "effort": "high|medium|low",
      "affected_components": ["componentName"]
    }
  ],
  "strengths": [
    { "title": "string", "description": "string" }
  ],
  "confidence": "high|medium|low",
  "model_metadata": {
    "model": "claude-sonnet-4-6",
    "tokens_in": 0,
    "tokens_out": 0,
    "duration_ms": 0
  }
}
```

The schema is published as a JSON Schema document in `infrastructure/contracts/analysis-report.schema.json` and validated by smart-service before publishing the result, and by orchestrator before persisting.

## 8. API contracts

### 8.1 Public REST — gateway (`/api/v1`)

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `POST` | `/auth/register` | — | Body `{email, password, displayName}` → `201 {userId}` |
| `POST` | `/auth/login` | — | → `200 {accessToken, refreshToken, expiresIn}` |
| `POST` | `/auth/refresh` | refresh | Rotate access token |
| `POST` | `/auth/logout` | bearer | Revoke refresh token |
| `POST` | `/asset-bundles` | bearer | Create empty bundle → `201 {bundleId, status:"INITIATED"}` |
| `POST` | `/asset-bundles/{id}/assets` | bearer | `multipart/form-data`, repeatable `files`. Validates count/size/type. → `201` |
| `POST` | `/asset-bundles/{id}/finalize` | bearer | Closes bundle, triggers session creation. → `202 {sessionId, state:"ASSETS_UPLOADED"}` |
| `GET` | `/asset-bundles/{id}` | bearer (owner) | Bundle + assets |
| `GET` | `/sessions/{id}` | bearer (owner) | Session state |
| `GET` | `/sessions/{id}/report` | bearer (owner) | Full report; `409` if not `REPORT_READY` |
| `POST` | `/sessions/{id}/cancel` | bearer (owner) | → `202` |

**Errors:** RFC 7807 `application/problem+json`. Codes: `400, 401, 403, 404, 409, 413, 415, 422, 429, 500, 503`.

**Rate limiting:** Bucket4j on `POST /asset-bundles/*/assets` and `/auth/login`. 60 req/min/user; 10 req/min/IP unauthenticated.

### 8.2 WebSocket — gateway

```
wss://gateway/ws/sessions/{sessionId}?token=<accessToken>
```

- JWT in query string; gateway validates and verifies session ownership before upgrade.
- Server frames: `session.snapshot` on connect (last N events), `session.event` on each transition, `ping` every 25 s.
- Client frames: only `pong`. Cancellation goes through REST.
- Closure codes: `4401` invalid token, `4403` not owner, `4404` session gone, `1000` normal close on terminal state.
- On reconnect, gateway replays the missing tail from its own `session_event_log` (the SQS consumer writes there) so the client never misses a transition.

### 8.3 Internal REST — orchestrator (HMAC-only, internal network)

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/internal/sessions` | Body `{sessionId, userId, assetCount, assetKeys[]}`; idempotent on `sessionId` |
| `GET` | `/internal/sessions/{id}` | Full session + latest event |
| `POST` | `/internal/sessions/{id}/cancel` | Cancel non-terminal session |
| `GET` | `/internal/sessions/{id}/report` | Persisted report or 404 |

**Internal auth:** `X-Internal-Signature: <hmac-sha256>` over `timestamp + method + path + sha256(body)` using a shared secret. Replay window 5 min. Enforced by `InternalHmacFilter`.

### 8.4 Messaging contracts

**`analysis-jobs`** (orchestrator → smart):
```json
{
  "schemaVersion": 1,
  "jobId": "uuid",
  "sessionId": "uuid",
  "userId": "uuid",
  "assets": [{ "assetId":"uuid", "s3Key":"...", "contentType":"...", "filename":"...", "sizeBytes":0 }],
  "promptVersion": "v1",
  "submittedAt": "ISO8601"
}
```

**`analysis-results`** (smart → orchestrator):
```json
{
  "schemaVersion": 1,
  "jobId": "uuid",
  "sessionId": "uuid",
  "status": "STARTED|SUCCEEDED|FAILED",
  "result": { /* full Q8 schema, present iff SUCCEEDED */ },
  "error": { "code": "...", "message": "..." },
  "modelMetadata": { "model":"...", "tokensIn":0, "tokensOut":0, "durationMs":0 },
  "completedAt": "ISO8601"
}
```

**`session-events` SNS topic** (orchestrator → fan-out → per-gateway SQS):
```json
{
  "schemaVersion": 1,
  "eventId": "uuid",
  "sessionId": "uuid",
  "userId": "uuid",
  "fromState": "QUEUED_FOR_ANALYSIS",
  "toState": "ANALYZING",
  "payload": {},
  "occurredAt": "ISO8601"
}
```

SNS message attributes: `sessionId`, `userId`, `toState` (filter-ready). DLQ after 3 receives on every queue. Idempotency keys: `jobId` for jobs, `eventId` for events.

### 8.5 OpenAPI surfaces
- gateway-service: `/v3/api-docs` + `/swagger-ui.html` (public, no auth).
- orchestrator-service: `/v3/api-docs` (internal network only).
- smart-service: `/openapi.json` + `/docs` (internal network only).

## 9. End-to-end flow

```
Client                Gateway              Orchestrator          Smart-svc        S3/SNS/SQS
  │                     │                      │                     │                │
  │── POST /asset-bundles ───────────────────▶│
  │   201 {bundleId} ◀──│
  │── POST /assets (multipart) ────────────────────────────────────────────────────────▶ S3 PUT
  │   201 ◀─────────────│
  │── POST /finalize ──▶│
  │                     │── POST /internal/sessions ─────▶│
  │                     │                                  │ TX: insert session(ASSETS_UPLOADED)
  │                     │                                  │     insert outbox[SNS event=ASSETS_UPLOADED]
  │                     │                                  │     insert outbox[SQS analysis-job]
  │                     │                                  │ OutboxRelay → SNS session-events (event=ASSETS_UPLOADED)
  │                     │                                  │ OutboxRelay → SQS analysis-jobs
  │                     │                                  │   on success: TX transition → QUEUED_FOR_ANALYSIS,
  │                     │                                  │     insert outbox[SNS event=QUEUED_FOR_ANALYSIS]
  │                     │                                  │ OutboxRelay → SNS session-events (event=QUEUED_FOR_ANALYSIS)
  │   202 {sessionId} ◀│
  │── WS /ws/sessions/{id} ─▶│ snapshot + live events
  │                     │◀── SQS session-events ────────── SNS fanout
  │                                                       smart-svc consumes ─▶
  │                                                       publishes STARTED ──▶ analysis-results
  │                                                       reads S3, calls Claude
  │                                                       publishes SUCCEEDED ─▶ analysis-results
  │                     │                      │◀── SQS analysis-results ──
  │                     │                      │ persist report
  │                     │                      │ → ANALYSIS_COMPLETED → REPORT_READY
  │                     │                      │ outbox publisher ─▶ SNS session-events
  │                     │◀── session-events ───│
  │   WS frame ◀────────│
  │── GET /sessions/{id}/report ─▶│
  │   200 {full report} ◀────────│
```

The orchestrator advances `QUEUED_FOR_ANALYSIS → ANALYZING` on receipt of a `STARTED` `analysis-results` message from smart-service, avoiding races with model latency.

### 9.1 Authoritative state transitions

| From | Trigger | To |
|---|---|---|
| — | `POST /internal/sessions` | `CREATED` (transient) → `ASSETS_UPLOADED` |
| `ASSETS_UPLOADED` | `OutboxRelay` confirms `analysis-jobs` SQS publish; opens a fresh tx to advance state and append the next outbox event | `QUEUED_FOR_ANALYSIS` |
| `QUEUED_FOR_ANALYSIS` | `analysis-results` `STARTED` | `ANALYZING` |
| `ANALYZING` | `analysis-results` `SUCCEEDED` | `ANALYSIS_COMPLETED` |
| `ANALYSIS_COMPLETED` | report row persisted | `REPORT_READY` |
| any non-terminal | `POST /internal/sessions/{id}/cancel` | `CANCELED` |
| any non-terminal | `analysis-results` `FAILED` after retries; or DLQ tripped | `FAILED` |

Transitions enforced by `SessionStateMachine` (pure domain). Illegal transitions throw `IllegalSessionTransitionException` → `409` from internal REST.

## 10. Failure handling

### 10.1 Retries

| Operation | Strategy |
|---|---|
| Gateway → S3 PUT | AWS SDK default (3 attempts, exp backoff). On final failure: bundle → `FAILED`. |
| Gateway → orchestrator REST | Resilience4j: 3 attempts, 200 ms initial, 2× backoff, jitter; CB 50% over 20 calls → open 30 s. |
| Outbox → SNS/SQS publish | Poller retries forever with exp backoff capped at 60 s. `published_at IS NULL` until success. |
| Smart-svc Anthropic call | 3 attempts on 429/5xx; non-retryable 4xx fail-fast. |
| SQS consumer (any) | Visibility 5 min; 3 receives → DLQ. CloudWatch alarm in prod; locally log + metric. |
| DLQ replay | `POST /admin/replay/{queue}` (internal HMAC) on smart-svc and orchestrator. |

### 10.2 Failure → user-visible state

| Failure | Outcome |
|---|---|
| Asset PUT fails | Bundle → `FAILED`; finalize returns `409`. |
| Orchestrator unreachable on finalize | Gateway returns `503`; bundle stays `UPLOADED`; finalize is idempotent so client can retry. |
| Smart-svc crash mid-analysis | SQS visibility expires; redelivery; dedup prevents double Anthropic charge. |
| Anthropic returns malformed JSON | Smart-svc retries with stricter prompt; on exhaust, `FAILED` `MODEL_OUTPUT_INVALID`. |
| Anthropic 429 sustained | Backoff; on exhaust, `FAILED` `MODEL_RATE_LIMITED`. |
| Result message lost | DLQ trips; on-call replays via admin endpoint. |
| WS disconnect | Client reconnects; server replays last N events on snapshot frame. |

## 11. Cross-cutting

### 11.1 Security
- JWT RS256, 15-min access, 7-day refresh with rotation; revocation list per session.
- bcrypt cost 12.
- Internal HMAC-SHA256 with 5-min replay window.
- S3 SSE-S3 encryption at rest (LocalStack-compatible flag set; real AWS uses SSE-KMS).
- All inter-service traffic confined to docker network in dev.
- Secrets via env in dev; production placeholder only — no real cloud secret manager wiring.

### 11.2 Observability
- Spring services: Micrometer Observation API → OpenTelemetry bridge → OTLP exporter → OTel Collector. Produces metrics + traces from one instrumentation surface (HTTP, JDBC, WebClient, scheduled tasks).
- Python service: OpenTelemetry SDK directly (auto-instrumentations for FastAPI, httpx, SQLAlchemy, boto3) → OTLP.
- Logs: structured JSON via Logback (Spring) and `structlog` (Python), shipped to OTel Collector → Loki.
- Spans of interest per session: `gateway.upload`, `gateway.finalize`, `orchestrator.create_session`, `orchestrator.publish_job`, `smart.consume_job`, `smart.call_anthropic`, `smart.publish_result`, `orchestrator.consume_result`, `gateway.broadcast_ws`. W3C `traceparent` propagated across REST and SQS message attributes — every session yields one trace from upload to WS push.
- Metrics: per-state count, transition latency histogram, queue depth, Anthropic latency, token usage, WS connection count.
- Grafana dashboards provisioned: one per service + a "session lifecycle" dashboard.

### 11.3 Idempotency & concurrency
- `bundleId`, `sessionId`, `jobId`, `eventId` all pre-known UUIDs.
- Every state-changing internal endpoint idempotent on its primary key.
- `sessions.version` (JPA `@Version`); on conflict, re-read and retry once before surfacing `409`.

## 12. Testing strategy

### 12.1 Unit tests
- Domain layer ≥ 90% branch coverage. State machine, validators, value objects, port contracts (with hand-written fakes).
- Application services tested with in-memory port fakes (no mocking framework needed).
- JUnit 5 + AssertJ (Spring); pytest + hypothesis for state-machine property tests (Python).

### 12.2 Integration tests (per service)
- Spring services: Testcontainers — Postgres + LocalStack (S3, SNS, SQS); migrations run per container; `@SpringBootTest` + `WebTestClient`.
- Smart-service: Testcontainers-Python — Postgres + LocalStack. Anthropic replaced with VCR-style recorded cassettes; live calls only on opt-in `@pytest.mark.live` lane.
- Coverage of every adapter: persistence round-trip, S3 up/download, SQS publish + consume, HMAC filter (positive + negative), JWT issuance + validation.

### 12.3 Contract tests
- Pact: gateway (consumer) ↔ orchestrator internal REST (provider).
- JSON-schema-based contract tests for every SQS payload, with the schema files stored in `infrastructure/contracts/`.

### 12.4 End-to-end tests
- Python harness in `infrastructure/e2e/`: brings up full compose, registers user, uploads fixture PDF, listens to WebSocket until `REPORT_READY`, validates report against the JSON schema, tears down.
- Anthropic stubbed by `FakeAnalysisModel` adapter activated via `SMART_SERVICE_PROFILE=e2e`.
- One nightly "live" e2e job runs against real Anthropic on a small fixture set, gated on a CI secret.

### 12.5 Frontend tests
- Vitest for components.
- Playwright happy-path browser test against the running compose.

### 12.6 Performance smoke (optional, on demand)
- k6 script: 10 concurrent uploads; assert p95 finalize < 2 s; p95 WS first event < 5 s.

## 13. CI

Five GitHub Actions workflows in `.github/workflows/`:

| Workflow | Trigger | Pipeline |
|---|---|---|
| `ci-gateway.yml` | PR touching `gateway-service/**` or shared schemas | build → unit → integration → pact verify → image build → push to GHCR `:sha` + `:branch` |
| `ci-orchestrator.yml` | PR touching `orchestrator-service/**` | same |
| `ci-smart.yml` | PR touching `smart-service/**` | uv sync → ruff → mypy → pytest → image build & push |
| `ci-frontend.yml` | PR touching `frontend/**` | npm ci → eslint → vitest → build → image build & push |
| `e2e.yml` | push to `main`, nightly cron | docker compose up → e2e harness → upload logs as artifact |

Caches: Gradle, uv, npm keyed by lockfile hashes. Path filters keep PRs fast. Branch protection: 1 review, signed commits, no force-push, all relevant `ci-*` required. `e2e.yml` gates production image promotion (re-tag `:sha` → `:stable`).

## 14. Repository layout

```
fiap-secure-systems/
├── README.md
├── Makefile                                # up / down / logs / test / migrate / seed
├── docker-compose.yml
├── docker-compose.observability.yml        # opt-in: tempo + loki + prometheus + grafana
├── .env.example
├── .github/workflows/
├── docs/
│   ├── superpowers/specs/                  # this design doc
│   └── architecture/                       # ADRs, PlantUML diagrams
├── infrastructure/
│   ├── localstack/init/                    # bootstrap topic, queues, bucket
│   ├── postgres/init/                      # CREATE DATABASE gateway_db / orchestrator_db / smart_db
│   ├── otel/                               # collector, tempo, prometheus, loki, grafana provisioning
│   ├── contracts/                          # JSON schemas for messaging payloads
│   └── e2e/                                # python harness + fixtures
├── gateway-service/
│   ├── Dockerfile
│   ├── build.gradle.kts
│   └── src/{main,test}/
├── orchestrator-service/
│   ├── Dockerfile
│   ├── build.gradle.kts
│   └── src/{main,test}/
├── smart-service/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── smart_service/
│   └── tests/
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── vite.config.ts
    └── src/
```

## 15. docker-compose

```yaml
services:
  postgres:        # one container, three logical DBs created via init scripts
  localstack:      # SQS + SNS + S3; init scripts create topic, queues, bucket
  otel-collector:  # receives OTLP from all three services
  gateway-service:
    depends_on: [postgres, localstack, otel-collector]
  orchestrator-service:
    depends_on: [postgres, localstack, otel-collector]
  smart-service:
    depends_on: [postgres, localstack, otel-collector]
    env: ANTHROPIC_API_KEY (.env, never committed)
  frontend:
    depends_on: [gateway-service]
# observability stack lives in docker-compose.observability.yml (opt-in via `make up-obs`)
```

Healthchecks on every service. `depends_on` uses `condition: service_healthy` for data-tier services. `make up` brings the stack online; `make e2e` runs the harness.

## 16. Out of scope (explicit)

- Multi-tenant isolation beyond user-owned sessions.
- Anthropic streaming responses.
- File deduplication across bundles.
- Asset preview / thumbnail generation.
- Admin UI — admin operations are CLI/HTTP only.
- Production secret-manager wiring beyond placeholder envs.
