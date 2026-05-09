# gateway-service

Public REST + WebSocket entry point for the fiap-secure-systems platform.

## Local development

- `make gw-build` — Gradle compile + bootJar
- `make gw-test-unit` — unit tests
- `make gw-test-integration` — Testcontainers integration tests
- `make gw-up` — start the full stack with gateway-service
- `make gw-logs` — tail container logs
- `make gw-shell` — exec a shell inside the running container
- `make gw-round-trip` — end-to-end register → finalize → REPORT_READY assertion

## Environment

The service reads its config from environment variables prefixed `GATEWAY_*`,
plus the platform-shared `AWS_*`, `INTERNAL_HMAC_SECRET`, and `OTEL_*`. See
`.env.example` for the full list.
