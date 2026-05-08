# orchestrator-service

Spring Boot 3.4 / Java 21 service that owns session lifecycle. Receives `POST /internal/sessions` from gateway-service (via internal HMAC), publishes `analysis-jobs` SQS via the transactional outbox, drives the `SessionStateMachine` from `analysis-results` SQS messages, and broadcasts every state transition as a `session-events` SNS event.

## Local development

```bash
./gradlew :orchestrator-service:bootRun                   # requires running Postgres + LocalStack
./gradlew :orchestrator-service:test                      # unit tests (no Docker)
./gradlew :orchestrator-service:integrationTest           # Testcontainers (Docker required)
./gradlew :orchestrator-service:check                     # both
```

## Environment

See `../.env.example`. The variables prefixed `ORCHESTRATOR_DB_` / `INTERNAL_HMAC_` / `SQS_` / `SNS_` / `OTEL_` apply here.
