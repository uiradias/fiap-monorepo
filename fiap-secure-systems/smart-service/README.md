# smart-service

FastAPI / Python 3.12 service that consumes `analysis-jobs`, reads asset bytes from S3, calls Anthropic Claude (or `FakeAnalysisModel` in `e2e` profile), validates the structured report, and publishes `STARTED` then `SUCCEEDED` (or `FAILED`) to the `analysis-results` SQS queue.

## Local development

```bash
uv sync
uv run pytest -m "not integration"          # unit tests only
uv run pytest -m "integration"              # spawns Testcontainers (Docker required)
uv run ruff check .
uv run mypy smart_service
uv run uvicorn smart_service.main:app --reload --port 8000
```

## Environment

See `../.env.example`. The variables prefixed `SMART_DB_` / `ANTHROPIC_` / `SMART_SERVICE_` apply here. `SMART_SERVICE_PROFILE=e2e` activates the `FakeAnalysisModel` so the service runs with no API key.

## RAG (grounded) analysis strategy

The baseline pipeline (single Sonnet call with prompt-engineered JSON) is
selected by default. Set `SMART_ANALYSIS_STRATEGY=grounded` to enable the
retrieval-augmented pipeline:

1. **Visual extraction** — Haiku 4.5 vision call produces a canonical component
   graph via tool-use.
2. **Canonicalisation** — Haiku refines any `unknown`-kinded components.
3. **Retrieval** — pgvector cosine search against the curated `corpus/seed/`
   patterns.
4. **Schema-bound emission** — Sonnet 4.6 with tool-use; risks must cite
   retrieved chunks. Uncited risks are dropped.

### Setup

```bash
# 1. Configure env vars
export SMART_ANALYSIS_STRATEGY=grounded
export VOYAGE_API_KEY=...
export ANTHROPIC_API_KEY=...

# 2. Make sure migrations have run
uv run alembic upgrade head

# 3. Ingest the seed corpus into Postgres
make smart-ingest-corpus      # docker compose path
# or, locally:
uv run smart-ingest-corpus
```

### Evaluate against the golden set

```bash
make smart-eval
```

Runs `pytest -m eval`. The eval harness lives under `tests/eval/` and scores
the grounded pipeline on five golden architectures (placeholders ship; replace
each `tests/eval/golden/<id>/architecture.png` with a real diagram to get a
meaningful score).

Reports produced by the grounded pipeline include a `citations` array on each
risk, pointing back to the corpus chunks that grounded the finding. The
baseline pipeline emits `risks` with empty `citations` — both shapes validate
against the same `analysis-report.schema.json`.
