# Contributing

## Local setup

Bring the full stack up:

```bash
make gen-jwt-keys              # generate gateway-service JWT keys
make up                        # postgres + localstack + otel-collector
make smart-up                  # add smart-service
make orch-up                   # add orchestrator-service
make gw-up                     # add gateway-service
make front-up                  # add frontend (nginx)
```

Verify with the four round-trip scripts:

```bash
make smoke                     # PASS=19/0 — Postgres roles + LocalStack queues + Tempo health
make round-trip                # smart-service synthetic SQS round-trip
make orch-round-trip           # POST /internal/sessions → REPORT_READY (note: orch-round-trip's session-event count assertion fails when the gateway is up — the gateway's SQS consumer drains the queue first; this is by design)
make gw-round-trip             # full HTTP register → finalize → REPORT_READY
make front-round-trip          # full SPA register → finalize → REPORT_READY (curl + WebSocket handshake)
```

For the front-end Playwright e2e:

```bash
make front-test-e2e            # runs Playwright against an already-running stack
make e2e                       # nukes, brings up the full stack, runs all four round-trips + Playwright, tears down
```

## CI

Per-service workflows live in `.github/workflows/ci-{smart,orchestrator,gateway,frontend}.yml` and are path-gated. The cross-cutting `e2e.yml` runs on every push to `main` and nightly at 03:00 UTC.

**Recommended branch protection on `main`:**
- Require PR review (1 reviewer)
- Require signed commits
- Require all `ci-*` checks for changed paths
- Require `e2e` check on the merge commit
- Disallow force-push

These are GitHub repository settings, not code — configure them in *Settings → Branches*.

## Conventions

- Plans live in `docs/superpowers/plans/YYYY-MM-DD-<topic>.md` and are NOT auto-committed by tooling — the human reviews and commits them.
- One commit per plan task. Commit messages use Conventional Commits: `feat(<scope>): ...`, `fix(<scope>): ...`, `chore(<scope>): ...`, `test(<scope>): ...`.
- TDD: tests come before code; watch the failing test fail before implementing.
