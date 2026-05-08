FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH=/opt/venv/bin:$PATH

# uv: small static binary
COPY --from=ghcr.io/astral-sh/uv:0.4 /uv /usr/local/bin/uv

WORKDIR /app

# 1. Cache deps
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-install-project

# 2. Install the project itself
COPY smart_service ./smart_service
COPY alembic.ini ./alembic.ini
RUN uv sync --frozen

# 3. Entrypoint runs migrations then uvicorn
COPY --chmod=0755 <<'SH' /app/entrypoint.sh
#!/usr/bin/env bash
set -euo pipefail
echo "[smart-service] running alembic upgrade head"
uv run alembic upgrade head
echo "[smart-service] starting uvicorn"
exec uv run uvicorn smart_service.main:app --host 0.0.0.0 --port 8000
SH

EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
