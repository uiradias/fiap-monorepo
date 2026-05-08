from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import boto3
import pytest
from testcontainers.localstack import LocalStackContainer

from smart_service.adapter.inbound.sqs_consumer import SqsAnalysisJobConsumer
from smart_service.adapter.outbound.fake_analysis_model import FakeAnalysisModel
from smart_service.application.analyze_assets_service import AnalyzeAssetsService
from smart_service.domain.model import AnalysisJob, AnalysisOutcome, Asset


class InMemoryReader:
    def read(self, asset: Asset) -> bytes:
        return b"\x89PNG"


class InMemoryRepo:
    def __init__(self) -> None:
        self._processed: set[UUID] = set()
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


class CapturingPublisher:
    def __init__(self) -> None:
        self.published: list[AnalysisOutcome] = []

    def publish(self, outcome: AnalysisOutcome) -> None:
        self.published.append(outcome)


@pytest.fixture(scope="module")
def localstack():
    with LocalStackContainer(image="localstack/localstack:3.5").with_services("sqs") as ls:
        yield ls


@pytest.fixture()
def queue_url(localstack):
    sqs = boto3.client(
        "sqs",
        endpoint_url=localstack.get_url(),
        region_name="us-east-1",
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )
    # Use a fresh queue per test to avoid cross-test interference
    name = f"analysis-jobs-{uuid4().hex[:8]}"
    url = sqs.create_queue(QueueName=name)["QueueUrl"]
    return sqs, url


@pytest.mark.integration
def test_consumer_processes_message(localstack, queue_url, repo_root: Path):
    sqs, url = queue_url
    job_id = uuid4()
    session_id = uuid4()
    body = {
        "schemaVersion": 1,
        "jobId": str(job_id),
        "sessionId": str(session_id),
        "userId": str(uuid4()),
        "assets": [
            {
                "assetId": str(uuid4()),
                "s3Key": "sessions/x/img.png",
                "contentType": "image/png",
                "filename": "img.png",
                "sizeBytes": 4,
            }
        ],
        "promptVersion": "v1",
        "submittedAt": datetime.now(UTC).isoformat(),
    }
    sqs.send_message(QueueUrl=url, MessageBody=json.dumps(body))

    repo = InMemoryRepo()
    pub = CapturingPublisher()
    svc = AnalyzeAssetsService(
        asset_reader=InMemoryReader(),
        model=FakeAnalysisModel(),
        publisher=pub,
        repo=repo,
        model_id="fake-claude",
    )
    consumer = SqsAnalysisJobConsumer(
        endpoint_url=localstack.get_url(),
        region="us-east-1",
        access_key="test",
        secret_key="test",
        queue_url=url,
        application_service=svc,
        contracts_dir=repo_root / "infrastructure" / "contracts",
        long_poll_seconds=1,
        visibility_seconds=30,
    )

    consumer.start()
    deadline = time.time() + 15
    while time.time() < deadline and len(pub.published) < 2:
        time.sleep(0.2)
    consumer.stop(timeout=5)

    statuses = [o.status.value for o in pub.published]
    assert statuses == ["STARTED", "SUCCEEDED"]

    remaining = sqs.receive_message(QueueUrl=url, WaitTimeSeconds=1)
    assert "Messages" not in remaining


@pytest.mark.integration
def test_bad_uuid_message_is_dropped(localstack, queue_url, repo_root: Path):
    """A schema-shaped message with a non-UUID jobId must be dropped (not redriven)."""
    sqs, url = queue_url
    body = {
        "schemaVersion": 1,
        "jobId": "REPLACE_JOB",  # bad UUID — would crash worker without format check
        "sessionId": str(uuid4()),
        "userId": str(uuid4()),
        "assets": [
            {
                "assetId": str(uuid4()),
                "s3Key": "sessions/x/img.png",
                "contentType": "image/png",
                "filename": "img.png",
                "sizeBytes": 4,
            }
        ],
        "promptVersion": "v1",
        "submittedAt": datetime.now(UTC).isoformat(),
    }
    sqs.send_message(QueueUrl=url, MessageBody=json.dumps(body))

    repo = InMemoryRepo()
    pub = CapturingPublisher()
    svc = AnalyzeAssetsService(
        asset_reader=InMemoryReader(),
        model=FakeAnalysisModel(),
        publisher=pub,
        repo=repo,
        model_id="fake-claude",
    )
    consumer = SqsAnalysisJobConsumer(
        endpoint_url=localstack.get_url(),
        region="us-east-1",
        access_key="test",
        secret_key="test",
        queue_url=url,
        application_service=svc,
        contracts_dir=repo_root / "infrastructure" / "contracts",
        long_poll_seconds=1,
        visibility_seconds=30,
    )
    consumer.start()
    time.sleep(3)
    consumer.stop(timeout=5)

    assert pub.published == []
    remaining = sqs.receive_message(QueueUrl=url, WaitTimeSeconds=1)
    assert "Messages" not in remaining


@pytest.mark.integration
def test_invalid_message_is_dropped_and_logged(localstack, queue_url, repo_root: Path):
    """A payload that violates the JSON schema is deleted (no infinite redrive)."""
    sqs, url = queue_url
    sqs.send_message(QueueUrl=url, MessageBody='{"not": "valid"}')

    repo = InMemoryRepo()
    pub = CapturingPublisher()
    svc = AnalyzeAssetsService(
        asset_reader=InMemoryReader(),
        model=FakeAnalysisModel(),
        publisher=pub,
        repo=repo,
        model_id="fake-claude",
    )
    consumer = SqsAnalysisJobConsumer(
        endpoint_url=localstack.get_url(),
        region="us-east-1",
        access_key="test",
        secret_key="test",
        queue_url=url,
        application_service=svc,
        contracts_dir=repo_root / "infrastructure" / "contracts",
        long_poll_seconds=1,
        visibility_seconds=30,
    )
    consumer.start()
    time.sleep(3)
    consumer.stop(timeout=5)

    assert pub.published == []
    remaining = sqs.receive_message(QueueUrl=url, WaitTimeSeconds=1)
    assert "Messages" not in remaining
