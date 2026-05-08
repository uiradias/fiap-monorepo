from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from smart_service.adapter.outbound.fake_analysis_model import FakeAnalysisModel
from smart_service.application.analyze_assets_service import AnalyzeAssetsService
from smart_service.domain.model import (
    AnalysisJob,
    AnalysisOutcome,
    AnalysisStatus,
    Asset,
    ContentType,
    StructuredReport,
)
from smart_service.domain.ports import AnalysisModelError


class FakeAssetReader:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail

    def read(self, asset: Asset) -> bytes:
        if self.fail:
            raise RuntimeError("s3 down")
        return b"\x89PNG"


_FIXED_JOB_ID = UUID("11111111-1111-1111-1111-111111111111")


class FakeAuditRepo:
    def __init__(self, *, already: bool = False) -> None:
        self._processed: set[UUID] = set()
        if already:
            self._processed.add(_FIXED_JOB_ID)
        self.events: list[tuple[str, UUID]] = []

    def is_already_processed(self, job_id: UUID) -> bool:
        return job_id in self._processed

    def mark_processed(self, job_id: UUID) -> None:
        self._processed.add(job_id)
        self.events.append(("processed", job_id))

    def start_run(self, job: AnalysisJob, model: str) -> None:
        self.events.append(("started", job.job_id))

    def mark_succeeded(self, job_id, report, duration_ms: int) -> None:
        self.events.append(("succeeded", job_id))

    def mark_failed(self, job_id, error: str, duration_ms: int) -> None:
        self.events.append(("failed", job_id))


class FakePublisher:
    def __init__(self) -> None:
        self.published: list[AnalysisOutcome] = []

    def publish(self, outcome: AnalysisOutcome) -> None:
        self.published.append(outcome)


class FakeFailingModel:
    def analyze(self, job, asset_bytes):
        raise AnalysisModelError("MODEL_RATE_LIMITED", "429 sustained")


def _job(job_id: UUID = _FIXED_JOB_ID) -> AnalysisJob:
    return AnalysisJob(
        job_id=job_id,
        session_id=uuid4(),
        user_id=uuid4(),
        assets=(
            Asset(
                asset_id=uuid4(),
                s3_key="sessions/x/architecture.png",
                content_type=ContentType.IMAGE_PNG,
                filename="architecture.png",
                size_bytes=10,
            ),
        ),
        prompt_version="v1",
        submitted_at=datetime.now(UTC),
    )


def test_already_processed_is_silent_noop():
    repo = FakeAuditRepo(already=True)
    pub = FakePublisher()
    svc = AnalyzeAssetsService(
        asset_reader=FakeAssetReader(),
        model=FakeAnalysisModel(),
        publisher=pub,
        repo=repo,
        model_id="fake-claude",
    )
    svc.run(_job())
    assert pub.published == []
    assert repo.events == []


def test_happy_path_publishes_started_then_succeeded():
    repo = FakeAuditRepo()
    pub = FakePublisher()
    svc = AnalyzeAssetsService(
        asset_reader=FakeAssetReader(),
        model=FakeAnalysisModel(),
        publisher=pub,
        repo=repo,
        model_id="fake-claude",
    )
    svc.run(_job(uuid4()))

    statuses = [o.status for o in pub.published]
    assert statuses == [AnalysisStatus.STARTED, AnalysisStatus.SUCCEEDED]
    assert pub.published[1].report is not None
    assert isinstance(pub.published[1].report, StructuredReport)
    kinds = [e[0] for e in repo.events]
    assert kinds == ["started", "succeeded", "processed"]


def test_model_failure_publishes_started_then_failed():
    repo = FakeAuditRepo()
    pub = FakePublisher()
    svc = AnalyzeAssetsService(
        asset_reader=FakeAssetReader(),
        model=FakeFailingModel(),
        publisher=pub,
        repo=repo,
        model_id="fake-claude",
    )
    svc.run(_job(uuid4()))

    assert [o.status for o in pub.published] == [
        AnalysisStatus.STARTED,
        AnalysisStatus.FAILED,
    ]
    assert pub.published[1].failure is not None
    assert pub.published[1].failure.code == "MODEL_RATE_LIMITED"
    kinds = [e[0] for e in repo.events]
    assert kinds == ["started", "failed", "processed"]


def test_asset_read_failure_publishes_started_then_failed():
    repo = FakeAuditRepo()
    pub = FakePublisher()
    svc = AnalyzeAssetsService(
        asset_reader=FakeAssetReader(fail=True),
        model=FakeAnalysisModel(),
        publisher=pub,
        repo=repo,
        model_id="fake-claude",
    )
    svc.run(_job(uuid4()))

    assert [o.status for o in pub.published] == [
        AnalysisStatus.STARTED,
        AnalysisStatus.FAILED,
    ]
    assert pub.published[1].failure is not None
    assert pub.published[1].failure.code == "ASSET_READ_FAILED"
