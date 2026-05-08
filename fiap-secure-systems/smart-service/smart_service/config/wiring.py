"""Composition root. Builds all adapters and the application service from Settings."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import anthropic
from sqlalchemy import Engine

from smart_service.adapter.inbound.sqs_consumer import SqsAnalysisJobConsumer
from smart_service.adapter.outbound.claude_model_adapter import ClaudeModelAdapter
from smart_service.adapter.outbound.dlq_replayer import SqsDlqReplayer
from smart_service.adapter.outbound.fake_analysis_model import FakeAnalysisModel
from smart_service.adapter.outbound.postgres_audit_repository import (
    PostgresAuditRepository,
)
from smart_service.adapter.outbound.s3_asset_reader import S3AssetReader
from smart_service.adapter.outbound.sqs_result_publisher import SqsResultPublisher
from smart_service.application.analyze_assets_service import AnalyzeAssetsService
from smart_service.config.settings import Profile, Settings
from smart_service.domain.ports import AnalysisModelPort
from smart_service.infrastructure.db import build_engine


@dataclass(frozen=True, slots=True)
class Components:
    engine: Engine
    consumer: SqsAnalysisJobConsumer
    replayer: SqsDlqReplayer


def build_components(settings: Settings, *, contracts_dir: Path) -> Components:
    engine = build_engine(settings.smart_database_url)
    repo = PostgresAuditRepository(engine=engine)
    reader = S3AssetReader(
        endpoint_url=settings.aws_endpoint_url,
        region=settings.aws_region,
        access_key="test",
        secret_key="test",
        bucket=settings.s3_bucket,
    )
    publisher = SqsResultPublisher(
        endpoint_url=settings.aws_endpoint_url,
        region=settings.aws_region,
        access_key="test",
        secret_key="test",
        queue_url=settings.sqs_analysis_results_url,
        contracts_dir=contracts_dir,
    )
    model: AnalysisModelPort
    if settings.profile is Profile.E2E or settings.anthropic_api_key is None:
        model = FakeAnalysisModel(model_id=settings.anthropic_model)
    else:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key.get_secret_value())
        model = ClaudeModelAdapter(
            client=client, model=settings.anthropic_model, contracts_dir=contracts_dir,
        )

    svc = AnalyzeAssetsService(
        asset_reader=reader,
        model=model,
        publisher=publisher,
        repo=repo,
        model_id=settings.anthropic_model,
    )
    consumer = SqsAnalysisJobConsumer(
        endpoint_url=settings.aws_endpoint_url,
        region=settings.aws_region,
        access_key="test",
        secret_key="test",
        queue_url=settings.sqs_analysis_jobs_url,
        application_service=svc,
        contracts_dir=contracts_dir,
        long_poll_seconds=settings.sqs_long_poll_seconds,
        visibility_seconds=settings.sqs_visibility_seconds,
    )
    replayer = SqsDlqReplayer(
        endpoint_url=settings.aws_endpoint_url,
        region=settings.aws_region,
        access_key="test",
        secret_key="test",
    )
    return Components(engine=engine, consumer=consumer, replayer=replayer)
