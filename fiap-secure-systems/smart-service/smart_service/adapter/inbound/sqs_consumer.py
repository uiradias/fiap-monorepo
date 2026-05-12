"""Long-poll SQS consumer for analysis-jobs. Runs in its own thread."""
from __future__ import annotations

import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

import boto3
from botocore.config import Config
from opentelemetry import context as otel_context, trace
from opentelemetry.propagate import extract

from smart_service.adapter.schema.validation import (
    SchemaValidationError,
    validate_analysis_job,
)
from smart_service.application.analyze_assets_service import AnalyzeAssetsService
from smart_service.domain.model import AnalysisJob, Asset, ContentType

log = logging.getLogger(__name__)


class SqsAnalysisJobConsumer:
    """Polls analysis-jobs and dispatches each message to AnalyzeAssetsService.

    Thread-based so it can run alongside FastAPI's asyncio loop without bridging.
    """

    def __init__(
        self,
        *,
        endpoint_url: str,
        region: str,
        access_key: str,
        secret_key: str,
        queue_url: str,
        application_service: AnalyzeAssetsService,
        contracts_dir: Path,
        long_poll_seconds: int = 20,
        visibility_seconds: int = 300,
    ) -> None:
        cfg = Config(
            connect_timeout=10,
            read_timeout=long_poll_seconds + 10,
            retries={"max_attempts": 3, "mode": "standard"},
        )
        self._sqs = boto3.client(
            "sqs",
            endpoint_url=endpoint_url,
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=cfg,
        )
        self._queue_url = queue_url
        self._svc = application_service
        self._contracts_dir = contracts_dir
        self._long_poll_seconds = long_poll_seconds
        self._visibility_seconds = visibility_seconds
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None:
            raise RuntimeError("already started")
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="sqs-consumer", daemon=True)
        self._thread.start()
        log.info("sqs-consumer started queue_url=%s", self._queue_url)

    def stop(self, *, timeout: float = 30.0) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
            self._thread = None
        log.info("sqs-consumer stopped")

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self._poll_once()
            except Exception:
                log.exception("sqs-consumer poll failed; will retry")

    def _poll_once(self) -> None:
        resp = self._sqs.receive_message(
            QueueUrl=self._queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=self._long_poll_seconds,
            VisibilityTimeout=self._visibility_seconds,
            MessageAttributeNames=["All"],
        )
        for msg in resp.get("Messages", []):
            self._handle(dict(msg))

    def _handle(self, msg: dict[str, Any]) -> None:
        body = msg.get("Body", "")
        receipt = msg["ReceiptHandle"]
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            log.error("dropping non-JSON message body_head=%r", body[:200])
            self._delete(receipt)
            return

        try:
            validate_analysis_job(payload, self._contracts_dir)
        except SchemaValidationError as e:
            log.error("dropping invalid analysis-job message error=%s", e)
            self._delete(receipt)
            return

        try:
            job = _payload_to_job(payload)
        except (ValueError, KeyError, TypeError) as e:
            # Defense in depth: even after schema validation, a bad UUID or
            # datetime would only surface here. Drop the message instead of
            # letting it loop on redelivery until DLQ.
            log.error("dropping unparseable analysis-job message error=%s", e)
            self._delete(receipt)
            return

        carrier = {
            name: attr.get("StringValue", "")
            for name, attr in msg.get("MessageAttributes", {}).items()
        }
        parent_ctx = extract(carrier)
        token = otel_context.attach(parent_ctx)
        try:
            tracer = trace.get_tracer("smart-service.sqs-consumer")
            with tracer.start_as_current_span(
                "analysis-jobs process",
                kind=trace.SpanKind.CONSUMER,
            ):
                self._svc.run(job)
                self._delete(receipt)
        except Exception:
            log.exception("processing failed; leaving message for redelivery")
        finally:
            otel_context.detach(token)

    def _delete(self, receipt: str) -> None:
        self._sqs.delete_message(QueueUrl=self._queue_url, ReceiptHandle=receipt)


def _payload_to_job(p: dict[str, Any]) -> AnalysisJob:
    return AnalysisJob(
        job_id=UUID(p["jobId"]),
        session_id=UUID(p["sessionId"]),
        user_id=UUID(p["userId"]),
        assets=tuple(
            Asset(
                asset_id=UUID(a["assetId"]),
                s3_key=a["s3Key"],
                content_type=ContentType(a["contentType"]),
                filename=a["filename"],
                size_bytes=a["sizeBytes"],
            )
            for a in p["assets"]
        ),
        prompt_version=p["promptVersion"],
        submitted_at=datetime.fromisoformat(p["submittedAt"]),
    )
