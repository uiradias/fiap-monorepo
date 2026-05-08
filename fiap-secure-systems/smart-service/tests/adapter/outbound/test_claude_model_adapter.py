from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock
from uuid import uuid4

import anthropic
import pytest

from smart_service.adapter.outbound.claude_model_adapter import ClaudeModelAdapter
from smart_service.domain.model import AnalysisJob, Asset, ContentType
from smart_service.domain.ports import AnalysisModelError


def _job() -> AnalysisJob:
    return AnalysisJob(
        job_id=uuid4(),
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


def _mock_anthropic_response(text: str, *, usage_in=42, usage_out=84) -> MagicMock:
    m = MagicMock()
    m.content = [MagicMock(type="text", text=text)]
    m.usage = MagicMock(input_tokens=usage_in, output_tokens=usage_out)
    m.model = "claude-sonnet-4-6"
    return m


def test_returns_structured_report(contracts_dir: Path):
    fake_client = MagicMock(spec=anthropic.Anthropic)
    fake_client.messages.create.return_value = _mock_anthropic_response(
        '{"summary":"two-tier system with API and DB",'
        '"components":[{"name":"api","kind":"service","responsibility":"request handling",'
        '"relevance":"high","evidence":"labelled box on diagram"}],'
        '"risks":[{"title":"no auth","category":"security","severity":"high",'
        '"description":"no auth shown","affected_components":["api"],"recommendation":"add JWT"}],'
        '"improvements":[{"title":"add CDN","rationale":"static assets",'
        '"impact":"medium","effort":"low","affected_components":["api"]}],'
        '"strengths":[{"title":"simple","description":"easy to understand"}],'
        '"confidence":"medium","model_metadata":{"model":"claude-sonnet-4-6"}}'
    )
    adapter = ClaudeModelAdapter(
        client=fake_client,
        model="claude-sonnet-4-6",
        contracts_dir=contracts_dir,
    )
    job = _job()
    report = adapter.analyze(job, asset_bytes={job.assets[0].asset_id: b"\x89PNG\r\n\x1a\nfake"})
    assert report.summary.startswith("two-tier")
    assert report.confidence.value == "medium"
    assert report.model_metadata.tokens_in == 42
    assert report.model_metadata.tokens_out == 84


def test_uses_prompt_caching_on_system_block(contracts_dir: Path):
    """The system block must carry cache_control to enable prompt caching."""
    fake_client = MagicMock(spec=anthropic.Anthropic)
    fake_client.messages.create.return_value = _mock_anthropic_response(
        '{"summary":"x","components":[],"risks":[],"improvements":[],"strengths":[],'
        '"confidence":"low","model_metadata":{"model":"claude-sonnet-4-6"}}'
    )
    adapter = ClaudeModelAdapter(
        client=fake_client, model="claude-sonnet-4-6", contracts_dir=contracts_dir,
    )
    job = _job()
    adapter.analyze(job, asset_bytes={job.assets[0].asset_id: b"png"})

    kwargs = fake_client.messages.create.call_args.kwargs
    assert isinstance(kwargs["system"], list)
    sys_block = kwargs["system"][0]
    assert sys_block["type"] == "text"
    assert sys_block["cache_control"] == {"type": "ephemeral"}


def test_raises_on_malformed_json(contracts_dir: Path):
    fake_client = MagicMock(spec=anthropic.Anthropic)
    fake_client.messages.create.return_value = _mock_anthropic_response("not json")
    adapter = ClaudeModelAdapter(
        client=fake_client, model="claude-sonnet-4-6", contracts_dir=contracts_dir,
    )
    job = _job()
    with pytest.raises(AnalysisModelError) as exc:
        adapter.analyze(job, asset_bytes={job.assets[0].asset_id: b"png"})
    assert exc.value.code == "MODEL_OUTPUT_INVALID"


def test_raises_on_schema_violation(contracts_dir: Path):
    fake_client = MagicMock(spec=anthropic.Anthropic)
    fake_client.messages.create.return_value = _mock_anthropic_response(
        '{"summary":"x","components":[],"risks":[],"improvements":[],"strengths":[],'
        '"confidence":"low"}'
    )
    adapter = ClaudeModelAdapter(
        client=fake_client, model="claude-sonnet-4-6", contracts_dir=contracts_dir,
    )
    job = _job()
    with pytest.raises(AnalysisModelError) as exc:
        adapter.analyze(job, asset_bytes={job.assets[0].asset_id: b"png"})
    assert exc.value.code == "MODEL_OUTPUT_INVALID"
