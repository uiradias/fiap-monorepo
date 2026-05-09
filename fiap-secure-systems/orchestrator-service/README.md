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

## Testcontainers + Docker Desktop on macOS

The integration test source set uses Testcontainers, which talks to the Docker daemon over its Unix socket. Some Docker Desktop releases (≥ 4.x) return incomplete `/info` responses to Testcontainers' Java HTTP client, causing `BadRequestException` at startup even though `docker info` and `docker compose` work fine in the shell.

The Gradle `integrationTest` task auto-detects `~/.docker/run/docker.sock` and exports it as `DOCKER_HOST` to the test JVM. If you still see Docker-related failures, try one of:

- Switch the Docker context to Colima or Lima (`brew install colima && colima start`).
- Run integration tests inside CI (Linux runners with `unix:///var/run/docker.sock` work out of the box).
- Set an explicit `DOCKER_HOST` environment variable before invoking Gradle.

The implementation is verified end-to-end by `make orch-round-trip` (Task 16), which uses Docker Compose directly and is unaffected by this Testcontainers quirk.
