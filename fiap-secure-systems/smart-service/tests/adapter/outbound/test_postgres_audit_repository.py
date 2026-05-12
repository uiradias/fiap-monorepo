from __future__ import annotations

import os
import subprocess
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from testcontainers.postgres import PostgresContainer

from smart_service.adapter.outbound.postgres_audit_repository import (
    PostgresAuditRepository,
)
from smart_service.domain.model import (
    AnalysisJob,
    Asset,
    Component,
    ComponentKind,
    Confidence,
    ContentType,
    ImpactEffort,
    Improvement,
    ModelMetadata,
    Relevance,
    Risk,
    RiskCategory,
    Severity,
    Strength,
    StructuredReport,
)


@pytest.fixture(scope="module")
def pg_engine():
    with PostgresContainer("pgvector/pgvector:pg16", driver="psycopg") as pg:
        url = pg.get_connection_url()
        env = {**os.environ, "SMART_DATABASE_URL": url}
        subprocess.run(
            ["uv", "run", "alembic", "upgrade", "head"],
            env=env, check=True, capture_output=True, text=True,
        )
        engine = create_engine(url)
        try:
            yield engine
        finally:
            engine.dispose()


def _job() -> AnalysisJob:
    return AnalysisJob(
        job_id=uuid4(),
        session_id=uuid4(),
        user_id=uuid4(),
        assets=(
            Asset(
                asset_id=uuid4(),
                s3_key="sessions/x/architecture.png",
                content_type=ContentType.IMAGE_PNG,
                filename="architecture.png",
                size_bytes=1024,
            ),
        ),
        prompt_version="v1",
        submitted_at=datetime.now(UTC),
    )


def _report() -> StructuredReport:
    return StructuredReport(
        summary="ok",
        confidence=Confidence.MEDIUM,
        components=(
            Component(
                name="api", kind=ComponentKind.SERVICE, responsibility="x",
                relevance=Relevance.HIGH, evidence="diagram",
            ),
        ),
        risks=(
            Risk(
                title="t", category=RiskCategory.SECURITY, severity=Severity.LOW,
                description="d", affected_components=("api",), recommendation="r",
            ),
        ),
        improvements=(
            Improvement(
                title="t", rationale="r", impact=ImpactEffort.LOW,
                effort=ImpactEffort.LOW, affected_components=("api",),
            ),
        ),
        strengths=(Strength(title="t", description="d"),),
        model_metadata=ModelMetadata(model="claude-sonnet-4-6", tokens_in=10, tokens_out=20),
    )


@pytest.mark.integration
def test_dedup_round_trip(pg_engine):
    engine = pg_engine
    repo = PostgresAuditRepository(engine=engine)

    job_id = uuid4()
    assert repo.is_already_processed(job_id) is False
    repo.mark_processed(job_id)
    assert repo.is_already_processed(job_id) is True


@pytest.mark.integration
def test_start_and_succeed(pg_engine):
    engine = pg_engine
    repo = PostgresAuditRepository(engine=engine)
    job = _job()

    repo.start_run(job, model="claude-sonnet-4-6")
    repo.mark_succeeded(job.job_id, _report(), duration_ms=1234)

    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT status, duration_ms, result IS NOT NULL AS has_result "
                 "FROM analysis_runs WHERE job_id = :jid"),
            {"jid": job.job_id},
        ).one()
    assert row.status == "SUCCEEDED"
    assert row.duration_ms == 1234
    assert row.has_result is True


@pytest.mark.integration
def test_start_and_fail(pg_engine):
    engine = pg_engine
    repo = PostgresAuditRepository(engine=engine)
    job = _job()

    repo.start_run(job, model="claude-sonnet-4-6")
    repo.mark_failed(job.job_id, error="boom", duration_ms=99)

    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT status, error, duration_ms FROM analysis_runs WHERE job_id = :jid"),
            {"jid": job.job_id},
        ).one()
    assert row.status == "FAILED"
    assert row.error == "boom"
    assert row.duration_ms == 99


@pytest.mark.integration
def test_mark_processed_is_idempotent(pg_engine):
    """Re-marking the same job_id must not raise."""
    engine = pg_engine
    repo = PostgresAuditRepository(engine=engine)
    job_id = uuid4()
    repo.mark_processed(job_id)
    repo.mark_processed(job_id)
    assert repo.is_already_processed(job_id) is True
