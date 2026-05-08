from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import boto3
import pytest
from testcontainers.localstack import LocalStackContainer

from smart_service.adapter.outbound.sqs_result_publisher import SqsResultPublisher
from smart_service.domain.model import (
    AnalysisFailure,
    AnalysisOutcome,
    AnalysisStatus,
    Component,
    ComponentKind,
    Confidence,
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
def localstack():
    with LocalStackContainer(image="localstack/localstack:3.5").with_services("sqs") as ls:
        yield ls


@pytest.fixture()
def queue(localstack):
    sqs = boto3.client(
        "sqs",
        endpoint_url=localstack.get_url(),
        region_name="us-east-1",
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )
    url = sqs.create_queue(QueueName="analysis-results")["QueueUrl"]
    return sqs, url


def _started(job_id, session_id) -> AnalysisOutcome:
    return AnalysisOutcome(
        job_id=job_id, session_id=session_id, status=AnalysisStatus.STARTED,
        completed_at=datetime.now(UTC),
    )


def _succeeded(job_id, session_id) -> AnalysisOutcome:
    md = ModelMetadata(model="claude-sonnet-4-6", tokens_in=10, tokens_out=20, duration_ms=100)
    return AnalysisOutcome(
        job_id=job_id, session_id=session_id, status=AnalysisStatus.SUCCEEDED,
        completed_at=datetime.now(UTC),
        report=StructuredReport(
            summary="ok",
            confidence=Confidence.HIGH,
            components=(
                Component(
                    name="api", kind=ComponentKind.SERVICE, responsibility="x",
                    relevance=Relevance.HIGH, evidence="d",
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
            model_metadata=md,
        ),
        model_metadata=md,
    )


def _failed(job_id, session_id) -> AnalysisOutcome:
    return AnalysisOutcome(
        job_id=job_id, session_id=session_id, status=AnalysisStatus.FAILED,
        completed_at=datetime.now(UTC),
        failure=AnalysisFailure(code="MODEL_OUTPUT_INVALID", message="malformed"),
    )


@pytest.mark.integration
def test_publishes_started(localstack, queue, repo_root: Path):
    sqs, url = queue
    pub = SqsResultPublisher(
        endpoint_url=localstack.get_url(), region="us-east-1",
        access_key="test", secret_key="test",
        queue_url=url, contracts_dir=repo_root / "infrastructure" / "contracts",
    )
    sid = uuid4()
    jid = uuid4()
    pub.publish(_started(jid, sid))

    msgs = sqs.receive_message(QueueUrl=url, WaitTimeSeconds=2)["Messages"]
    body = json.loads(msgs[0]["Body"])
    assert body["status"] == "STARTED"
    assert body["jobId"] == str(jid)


@pytest.mark.integration
def test_publishes_succeeded_with_report(localstack, queue, repo_root: Path):
    sqs, url = queue
    pub = SqsResultPublisher(
        endpoint_url=localstack.get_url(), region="us-east-1",
        access_key="test", secret_key="test",
        queue_url=url, contracts_dir=repo_root / "infrastructure" / "contracts",
    )
    sid = uuid4()
    jid = uuid4()
    pub.publish(_succeeded(jid, sid))

    msgs = sqs.receive_message(QueueUrl=url, WaitTimeSeconds=2)["Messages"]
    body = json.loads(msgs[0]["Body"])
    assert body["status"] == "SUCCEEDED"
    assert body["result"]["summary"] == "ok"
    assert body["modelMetadata"]["model"] == "claude-sonnet-4-6"


@pytest.mark.integration
def test_publishes_failed(localstack, queue, repo_root: Path):
    sqs, url = queue
    pub = SqsResultPublisher(
        endpoint_url=localstack.get_url(), region="us-east-1",
        access_key="test", secret_key="test",
        queue_url=url, contracts_dir=repo_root / "infrastructure" / "contracts",
    )
    sid = uuid4()
    jid = uuid4()
    pub.publish(_failed(jid, sid))

    msgs = sqs.receive_message(QueueUrl=url, WaitTimeSeconds=2)["Messages"]
    body = json.loads(msgs[0]["Body"])
    assert body["status"] == "FAILED"
    assert body["error"]["code"] == "MODEL_OUTPUT_INVALID"
