"""Publishes AnalysisOutcome to the analysis-results SQS queue. Implements ResultPublisherPort."""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import boto3

from smart_service.adapter.schema.validation import (
    SchemaValidationError,
    validate_analysis_result,
)
from smart_service.domain.model import (
    AnalysisOutcome,
    AnalysisStatus,
    StructuredReport,
)


class SqsResultPublisher:
    def __init__(
        self,
        *,
        endpoint_url: str,
        region: str,
        access_key: str,
        secret_key: str,
        queue_url: str,
        contracts_dir: Path,
    ) -> None:
        self._sqs = boto3.client(
            "sqs",
            endpoint_url=endpoint_url,
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )
        self._queue_url = queue_url
        self._contracts_dir = contracts_dir

    def publish(self, outcome: AnalysisOutcome) -> None:
        body = _outcome_to_message(outcome)
        try:
            validate_analysis_result(body, self._contracts_dir)
        except SchemaValidationError as e:
            raise RuntimeError(
                f"refusing to publish: outcome violates analysis-results schema: {e}"
            ) from e
        self._sqs.send_message(
            QueueUrl=self._queue_url,
            MessageBody=json.dumps(body, separators=(",", ":")),
            MessageAttributes={
                "sessionId": {"DataType": "String", "StringValue": str(outcome.session_id)},
                "status": {"DataType": "String", "StringValue": outcome.status.value},
            },
        )


def _outcome_to_message(outcome: AnalysisOutcome) -> dict[str, Any]:
    msg: dict[str, Any] = {
        "schemaVersion": 1,
        "jobId": str(outcome.job_id),
        "sessionId": str(outcome.session_id),
        "status": outcome.status.value,
        "completedAt": outcome.completed_at.isoformat(),
    }
    if outcome.status is AnalysisStatus.SUCCEEDED:
        if outcome.report is None or outcome.model_metadata is None:
            raise ValueError("SUCCEEDED outcome must carry a report and modelMetadata")
        msg["result"] = _report_to_jsonable(outcome.report)
        msg["modelMetadata"] = {
            "model": outcome.model_metadata.model,
            "tokensIn": outcome.model_metadata.tokens_in,
            "tokensOut": outcome.model_metadata.tokens_out,
            "durationMs": outcome.model_metadata.duration_ms,
        }
    elif outcome.status is AnalysisStatus.FAILED:
        if outcome.failure is None:
            raise ValueError("FAILED outcome must carry a failure")
        msg["error"] = {"code": outcome.failure.code, "message": outcome.failure.message}
    return msg


def _report_to_jsonable(report: StructuredReport) -> dict[str, Any]:
    def _enum_to_str(obj: Any) -> Any:
        if hasattr(obj, "value"):
            return obj.value
        if isinstance(obj, dict):
            return {k: _enum_to_str(v) for k, v in obj.items()}
        if isinstance(obj, list | tuple):
            return [_enum_to_str(x) for x in obj]
        return obj

    result: dict[str, Any] = _enum_to_str(asdict(report))
    # Preserve wire compatibility: omit `citations` key on risks where it's empty so
    # existing consumers (gateway, orchestrator) see an identical payload shape.
    for risk in result.get("risks", []):
        if not risk.get("citations"):
            risk.pop("citations", None)
    return result
