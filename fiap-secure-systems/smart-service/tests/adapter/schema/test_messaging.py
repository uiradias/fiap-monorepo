from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from jsonschema import Draft7Validator

from smart_service.adapter.schema.messaging import AnalysisJobMessage
from smart_service.adapter.schema.report import StructuredReportModel
from smart_service.adapter.schema.validation import (
    SchemaValidationError,
    validate_analysis_job,
    validate_analysis_result,
)


def _job_dict() -> dict:
    return {
        "schemaVersion": 1,
        "jobId": str(uuid4()),
        "sessionId": str(uuid4()),
        "userId": str(uuid4()),
        "assets": [
            {
                "assetId": str(uuid4()),
                "s3Key": "sessions/x/architecture.png",
                "contentType": "image/png",
                "filename": "architecture.png",
                "sizeBytes": 1024,
            }
        ],
        "promptVersion": "v1",
        "submittedAt": datetime.now(UTC).isoformat(),
    }


def test_pydantic_parses_a_valid_job():
    msg = AnalysisJobMessage.model_validate(_job_dict())
    assert msg.schemaVersion == 1
    assert msg.assets[0].contentType == "image/png"


def test_validator_accepts_a_valid_job(contracts_dir: Path):
    validate_analysis_job(_job_dict(), contracts_dir)


def test_validator_rejects_extra_field(contracts_dir: Path):
    payload = _job_dict()
    payload["extra"] = "no"
    with pytest.raises(SchemaValidationError):
        validate_analysis_job(payload, contracts_dir)


def test_pydantic_serializes_using_camelcase_aliases():
    payload = _job_dict()
    msg = AnalysisJobMessage.model_validate(payload)
    serialized = json.loads(msg.model_dump_json(by_alias=True))
    assert serialized["jobId"] == payload["jobId"]


def test_succeeded_result_requires_report(contracts_dir: Path):
    payload = {
        "schemaVersion": 1,
        "jobId": str(uuid4()),
        "sessionId": str(uuid4()),
        "status": "SUCCEEDED",
        "completedAt": datetime.now(UTC).isoformat(),
    }
    with pytest.raises(SchemaValidationError):
        validate_analysis_result(payload, contracts_dir)


def test_started_result_requires_no_report(contracts_dir: Path):
    payload = {
        "schemaVersion": 1,
        "jobId": str(uuid4()),
        "sessionId": str(uuid4()),
        "status": "STARTED",
        "completedAt": datetime.now(UTC).isoformat(),
    }
    validate_analysis_result(payload, contracts_dir)


def test_pydantic_report_model_matches_schema(contracts_dir: Path):
    """A minimal StructuredReportModel must validate against the JSON schema."""
    report_schema = json.loads((contracts_dir / "analysis-report.schema.json").read_text())
    Draft7Validator.check_schema(report_schema)
    minimal = {
        "summary": "x",
        "components": [],
        "risks": [],
        "improvements": [],
        "strengths": [],
        "confidence": "low",
        "model_metadata": {"model": "claude-sonnet-4-6"},
    }
    Draft7Validator(report_schema).validate(minimal)
    parsed = StructuredReportModel.model_validate(minimal)
    assert parsed.confidence == "low"
