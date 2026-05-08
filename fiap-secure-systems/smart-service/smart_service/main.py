"""smart-service entrypoint. FastAPI app + SQS consumer worker thread."""
from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import structlog
from fastapi import FastAPI

from smart_service.adapter.inbound.rest import build_router
from smart_service.config.settings import Settings
from smart_service.config.wiring import build_components
from smart_service.infrastructure.observability import (
    configure_logging,
    configure_tracing,
)


def _contracts_dir() -> Path:
    candidate = Path("/app/contracts")
    if candidate.is_dir():
        return candidate
    here = Path(__file__).resolve()
    for parent in here.parents:
        c = parent / "infrastructure" / "contracts"
        if c.is_dir():
            return c
    raise RuntimeError("infrastructure/contracts not found")


def create_app() -> FastAPI:
    settings = Settings()  # type: ignore[call-arg]
    configure_logging(settings.service_name)
    log = structlog.get_logger("smart-service.boot")

    contracts_dir = _contracts_dir()
    components = build_components(settings, contracts_dir=contracts_dir)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        components.consumer.start()
        log.info("smart-service started", profile=settings.profile.value)
        try:
            yield
        finally:
            components.consumer.stop(timeout=30.0)
            components.engine.dispose()
            log.info("smart-service stopped")

    app = FastAPI(title="smart-service", version="0.1.0", lifespan=lifespan)
    app.include_router(
        build_router(
            internal_hmac_secret=settings.internal_hmac_secret.get_secret_value(),
            replayer=components.replayer,
        )
    )
    configure_tracing(settings, app, components.engine)
    return app


app = create_app()
