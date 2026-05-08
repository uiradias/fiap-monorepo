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
