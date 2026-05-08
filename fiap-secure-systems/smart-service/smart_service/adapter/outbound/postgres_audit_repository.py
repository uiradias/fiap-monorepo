"""Postgres-backed implementation of AuditRepositoryPort."""
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Engine, text

from smart_service.domain.model import AnalysisJob, StructuredReport


class PostgresAuditRepository:
    """Implements `AuditRepositoryPort` (structural). Short-lived transactions only."""

    def __init__(self, *, engine: Engine) -> None:
        self._engine = engine

    def is_already_processed(self, job_id: UUID) -> bool:
        with self._engine.connect() as conn:
            row = conn.execute(
                text("SELECT 1 FROM processed_jobs WHERE job_id = :jid"),
                {"jid": job_id},
            ).first()
        return row is not None

    def mark_processed(self, job_id: UUID) -> None:
        # ON CONFLICT DO NOTHING — concurrent receipts of the same SQS message must not raise.
        with self._engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO processed_jobs (job_id, processed_at) "
                    "VALUES (:jid, :ts) ON CONFLICT (job_id) DO NOTHING"
                ),
                {"jid": job_id, "ts": datetime.now(UTC)},
            )

    def start_run(self, job: AnalysisJob, model: str) -> None:
        asset_keys = [a.s3_key for a in job.assets]
        with self._engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO analysis_runs "
                    "(id, session_id, job_id, status, asset_keys, prompt_version, "
                    "model, started_at) "
                    "VALUES (:id, :sid, :jid, 'RUNNING', CAST(:keys AS JSONB), "
                    ":pv, :model, :ts)"
                ),
                {
                    "id": uuid4(),
                    "sid": job.session_id,
                    "jid": job.job_id,
                    "keys": json.dumps(asset_keys),
                    "pv": job.prompt_version,
                    "model": model,
                    "ts": datetime.now(UTC),
                },
            )

    def mark_succeeded(
        self,
        job_id: UUID,
        report: StructuredReport,
        duration_ms: int,
    ) -> None:
        result_json = _report_to_jsonable(report)
        with self._engine.begin() as conn:
            conn.execute(
                text(
                    "UPDATE analysis_runs SET "
                    "status = 'SUCCEEDED', "
                    "result = CAST(:result AS JSONB), "
                    "tokens_in = :tin, tokens_out = :tout, "
                    "duration_ms = :dur, finished_at = :ts "
                    "WHERE job_id = :jid"
                ),
                {
                    "result": json.dumps(result_json),
                    "tin": report.model_metadata.tokens_in,
                    "tout": report.model_metadata.tokens_out,
                    "dur": duration_ms,
                    "ts": datetime.now(UTC),
                    "jid": job_id,
                },
            )

    def mark_failed(self, job_id: UUID, error: str, duration_ms: int) -> None:
        with self._engine.begin() as conn:
            conn.execute(
                text(
                    "UPDATE analysis_runs SET "
                    "status = 'FAILED', error = :err, "
                    "duration_ms = :dur, finished_at = :ts "
                    "WHERE job_id = :jid"
                ),
                {"err": error, "dur": duration_ms, "ts": datetime.now(UTC), "jid": job_id},
            )


def _report_to_jsonable(report: StructuredReport) -> dict[str, Any]:
    """Serialize a StructuredReport into the AI-output JSON shape (snake_case keys)."""
    def _enum_to_str(obj: Any) -> Any:
        if hasattr(obj, "value"):
            return obj.value
        if isinstance(obj, dict):
            return {k: _enum_to_str(v) for k, v in obj.items()}
        if isinstance(obj, list | tuple):
            return [_enum_to_str(x) for x in obj]
        return obj

    result: dict[str, Any] = _enum_to_str(asdict(report))
    return result
