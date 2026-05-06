# fiap-secure-systems — Implementation Roadmap

This document tracks the high-level decomposition of the project into sub-plans. Each sub-plan is its own document under `docs/superpowers/plans/` and produces working, verifiable software on its own. Update the **Status** column as sub-plans land.

**Source of truth:** [`docs/superpowers/specs/2026-05-05-fiap-secure-systems-design.md`](../specs/2026-05-05-fiap-secure-systems-design.md)

## Sub-plans

| # | Sub-plan | Plan file | Status | What's true at the end |
|---|---|---|---|---|
| **1** | **Foundation** | [`2026-05-06-foundation.md`](2026-05-06-foundation.md) | ✅ Complete; merged to `main` | `make up`/`make smoke`/`make up-obs` work cold-start. Postgres (3 DBs), LocalStack (S3 + SNS + SQS + DLQs), OTel Collector + Tempo/Prom/Loki/Grafana all healthy. Four JSON-schema contracts in `infrastructure/contracts/`. |
| **2** | **smart-service** | _to write_ | ⬜ Next | Python 3.12 / FastAPI / hex layout / Alembic. SQS consumer for `analysis-jobs`, S3 reader, Anthropic Claude adapter (with prompt caching), result publisher to `analysis-results`. Verifiable in isolation with synthetic SQS messages and `FakeAnalysisModel`. |
| **3** | **orchestrator-service** | _to write_ | ⬜ Pending sub-plan 2 | Spring Boot / hex layout / Flyway. Pure `SessionStateMachine`. Outbox + `OutboxRelay` (drains to SNS or SQS by `event_type`). Internal REST + `InternalHmacFilter`. AnalysisResult SQS consumer. End-to-end test: `POST /internal/sessions` → analysis-job published → smart-service runs → result consumed → state machine drives to `REPORT_READY` → SNS events published. |
| **4** | **gateway-service** | _to write_ | ⬜ Pending 2 + 3 | Spring Boot / hex layout. JWT auth (RS256, refresh tokens). Asset upload + S3 PUT. Internal HMAC signer for orchestrator calls. Finalize → orchestrator. `session_event_log` SQS consumer. WebSocket broadcaster on `/ws/sessions/{id}`. Full backend flow exercisable via curl + wscat. |
| **5** | **frontend** | _to write_ | ⬜ Pending 4 | React + Vite minimal SPA: register/login, upload page, session viewer with WebSocket. Browser flow against the running stack. |
| **6** | **CI + e2e + dashboards** | _to write_ | ⬜ Pending 1–5 | Five GitHub Actions workflows (per-service + e2e). Pact contract tests. Playwright e2e. Grafana dashboards (one per service + a session-lifecycle board). |

## Dependencies

```
1 (foundation) ──┬──▶ 2 (smart) ───┬──▶ 6 (CI/e2e)
                 ├──▶ 3 (orchestrator) ─┤
                 ├──▶ 4 (gateway) ─────┤
                 └──▶ 5 (frontend) ────┘
```

The application services in 2/3/4 are loosely coupled and could in principle parallelize, but writing them in numerical order keeps each sub-plan testable end-to-end against the previous output (smart-service alone, then orchestrator + smart, then gateway + the rest).

## Loose ends carried from foundation review

These were flagged by the final reviewer on `feat/foundation` and should be addressed in the appropriate sub-plan:

1. **Per-service Postgres roles** (sub-plan 2 onward) — currently all DBs are owned by the shared `postgres` superuser. Each service sub-plan should add `CREATE ROLE <service>_user; GRANT ... ON DATABASE <service>_db TO <service>_user;` (extend `infrastructure/postgres/init/`) and connect using that role.
2. **Tempo `search_enabled: true`** (sub-plan 2 or 3) — needed in `infrastructure/otel/tempo.yaml` once services start emitting traces, so the Grafana Trace Search UI works.
3. **SNS `RawMessageDelivery=true`** (sub-plan 4 — gateway) — gateway-side SQS consumer must expect raw JSON without the SNS envelope.
4. **`make ps` convenience target** — small Makefile addition for developer ergonomics; add when convenient.

## Plan-bug fixes baked into foundation (informational)

If future sub-plans bump versions, re-check these workarounds:

- OTel Collector contrib `0.103.0` is distroless — healthcheck uses `/otelcol-contrib validate` instead of `wget` (commented in `docker-compose.yml`).
- Loki `3.0.0` removed `chunks_directory`/`rules_directory` — uses single `filesystem.directory` (commented in `infrastructure/otel/loki.yaml`).

## Working conventions

- Each sub-plan lives at `docs/superpowers/plans/YYYY-MM-DD-<topic>.md`.
- Each sub-plan executes in an isolated worktree under `.worktrees/<branch-name>/`.
- Implementer + spec-compliance + code-quality reviews per task; final cold-start reproducibility check before merge.
- Author commits the integration commits (gitignore tweaks, merges) themselves; agents commit per-task work on the feature branch.
