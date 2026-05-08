from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from smart_service.adapter.outbound.fake_analysis_model import FakeAnalysisModel
from smart_service.domain.model import AnalysisJob, Asset, ContentType


def test_fake_returns_minimal_valid_report():
    job = AnalysisJob(
        job_id=uuid4(),
        session_id=uuid4(),
        user_id=uuid4(),
        assets=(
            Asset(
                asset_id=uuid4(),
                s3_key="sessions/x/img.png",
                content_type=ContentType.IMAGE_PNG,
                filename="img.png",
                size_bytes=10,
            ),
        ),
        prompt_version="v1",
        submitted_at=datetime.now(UTC),
    )
    fake = FakeAnalysisModel(model_id="fake-claude")
    report = fake.analyze(job, asset_bytes={job.assets[0].asset_id: b"x"})
    assert report.summary
    assert report.model_metadata.model == "fake-claude"
    assert any(c.evidence.startswith("(fake)") for c in report.components)
