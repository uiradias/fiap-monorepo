# Cross-service trace propagation

**Status:** approved (design), pending implementation
**Date:** 2026-05-12
**Scope:** backend only — three backend services (`gateway-service`, `orchestrator-service`, `smart-service`). Browser/SPA instrumentation is out of scope.

## Problem

After enabling Spring Boot Micrometer OTLP tracing in the two Java services (commit pending), all three backend services emit traces to Tempo, but **no trace spans more than one service**. A sample of 20 gateway traces showed zero containing child spans from orchestrator or smart-service.

The `session-lifecycle` Grafana dashboard depends on cross-service traces correlated through a session. Without propagation, end-to-end flows can't be visualized as one trace.

## Boundaries to instrument

| # | Producer → Consumer | Transport | Code path |
|---|---|---|---|
| 1 | gateway → orchestrator | HTTP (Spring `RestClient`) | `OrchestratorRestClient.java` |
| 2 | orchestrator → smart-service | SQS `analysis-jobs` | `SqsAnalysisJobPublisher.java` → `sqs_consumer.py` |
| 3 | smart-service → orchestrator | SQS `analysis-results` | `sqs_result_publisher.py` → `AnalysisResultSqsConsumer.java` |
| 4 | orchestrator → gateway | SNS `session-events` → SQS `session-events-gateway` | `SnsSessionEventPublisher.java` + `OutboxRelay` → gateway consumer |

## Approach

OpenTelemetry auto-instrumentation libraries, applied uniformly:

- **Java (orchestrator, gateway):** add `io.opentelemetry.instrumentation:opentelemetry-aws-sdk-2.2-autoconfigure`. Spring Boot's Micrometer OTel auto-config wires this into existing `SqsClient` / `SnsClient` beans transparently. Producer spans are emitted and `traceparent` is injected into SQS `MessageAttributes`; consumer spans extract it. No code changes to publishers/consumers.
- **Python (smart-service):** add `opentelemetry-instrumentation-botocore` to `pyproject.toml` and call `BotocoreInstrumentor().instrument()` once during startup (in `main.py` or `wiring.py`). Same producer/consumer behavior for boto3.
- **HTTP (boundary 1):** Spring `RestClient` is already auto-instrumented when Micrometer Tracing is on; verify via Tempo query before changing anything.
- **SNS → SQS (boundary 4):** subscription must use `RawMessageDelivery=true` so message attributes survive the SNS fan-out. Check the LocalStack bootstrap script; fix if not already set.

### Rejected alternatives

- **Manual W3C propagation at each call site.** ~30-50 lines per spot × 5 spots = more code, more tests, no observability win over auto-instrumentation. Rejected for diff size.
- **Mixed manual/auto.** Inconsistent. Rejected.

## Out of scope

- Browser OTel SDK in the SPA (the curl-based smoke test doesn't exercise the browser).
- OTLP metrics export (Prometheus panels remain empty).
- OTLP logs export (Loki panels remain empty).
- Business logic, SQS message bodies, HMAC signing, contract schemas — none touched.

## Verification

1. Run `make front-round-trip` and capture the returned `sessionId`.
2. Query Tempo for traces filtered by `service.name=gateway-service` from the past minute.
3. Pick the trace with a `POST /sessions/.../finalize` (or similar) root span.
4. Fetch the full trace by id; confirm it contains spans from all three services (`gateway-service`, `orchestrator-service`, `smart-service`).
5. Sanity-check the session-lifecycle Grafana dashboard for non-empty panels.

## Risks

- **Auto-instrumentation version coupling.** The OTel AWS SDK instrumentation must match the OTel BOM version (`1.42.1`). Mismatch causes either compile errors or silent no-ops. Mitigation: use the same group/BOM, pin a known-compatible version.
- **LocalStack SNS-SQS fan-out.** If `RawMessageDelivery=false`, message attributes are wrapped in the SNS envelope and the consumer-side extractor won't see `traceparent`. Mitigation: verify the LocalStack bootstrap and patch.
- **Smoke-test regression on first run after restart.** Cold-start of Java services warming JIT/Hibernate can cause `front-round-trip` to time out on its first invocation; second invocation succeeds. Already observed in prior session. Not a propagation issue.
