"""AnalyzeAssetsService — the use-case orchestrator. Pure application logic."""
from __future__ import annotations

import time
from datetime import UTC, datetime

from smart_service.domain.model import (
    AnalysisFailure,
    AnalysisJob,
    AnalysisOutcome,
    AnalysisStatus,
    ModelMetadata,
)
from smart_service.domain.ports import (
    AnalysisModelError,
    AnalysisModelPort,
    AssetReaderPort,
    AuditRepositoryPort,
    ResultPublisherPort,
)


class AnalyzeAssetsService:
    def __init__(
        self,
        *,
        asset_reader: AssetReaderPort,
        model: AnalysisModelPort,
        publisher: ResultPublisherPort,
        repo: AuditRepositoryPort,
        model_id: str,
    ) -> None:
        self._reader = asset_reader
        self._model = model
        self._publisher = publisher
        self._repo = repo
        self._model_id = model_id

    def run(self, job: AnalysisJob) -> None:
        if self._repo.is_already_processed(job.job_id):
            return  # silent ack — duplicate SQS delivery

        self._repo.start_run(job, model=self._model_id)
        self._publisher.publish(
            AnalysisOutcome(
                job_id=job.job_id,
                session_id=job.session_id,
                status=AnalysisStatus.STARTED,
                completed_at=datetime.now(UTC),
            )
        )

        started = time.monotonic()
        try:
            asset_bytes = {a.asset_id: self._reader.read(a) for a in job.assets}
        except Exception as e:
            self._finalize_failure(job, "ASSET_READ_FAILED", str(e), started)
            return

        try:
            report = self._model.analyze(job, asset_bytes)
        except AnalysisModelError as e:
            self._finalize_failure(job, e.code, e.message, started)
            return

        duration_ms = int((time.monotonic() - started) * 1000)
        self._repo.mark_succeeded(job.job_id, report, duration_ms=duration_ms)
        self._publisher.publish(
            AnalysisOutcome(
                job_id=job.job_id,
                session_id=job.session_id,
                status=AnalysisStatus.SUCCEEDED,
                completed_at=datetime.now(UTC),
                report=report,
                model_metadata=ModelMetadata(
                    model=report.model_metadata.model,
                    tokens_in=report.model_metadata.tokens_in,
                    tokens_out=report.model_metadata.tokens_out,
                    duration_ms=duration_ms,
                ),
            )
        )
        self._repo.mark_processed(job.job_id)

    def _finalize_failure(
        self,
        job: AnalysisJob,
        code: str,
        message: str,
        started_at: float,
    ) -> None:
        duration_ms = int((time.monotonic() - started_at) * 1000)
        self._repo.mark_failed(job.job_id, error=f"{code}: {message}", duration_ms=duration_ms)
        self._publisher.publish(
            AnalysisOutcome(
                job_id=job.job_id,
                session_id=job.session_id,
                status=AnalysisStatus.FAILED,
                completed_at=datetime.now(UTC),
                failure=AnalysisFailure(code=code, message=message),
            )
        )
        self._repo.mark_processed(job.job_id)
