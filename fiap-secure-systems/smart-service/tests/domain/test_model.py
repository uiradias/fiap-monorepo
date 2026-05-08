"""Domain model invariants. The domain layer must not import any framework."""
from __future__ import annotations

import importlib
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from smart_service.domain.model import (
    AnalysisJob,
    AnalysisStatus,
    Asset,
    Component,
    ComponentKind,
    Confidence,
    ContentType,
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


def _asset() -> Asset:
    return Asset(
        asset_id=uuid4(),
        s3_key="sessions/x/file.png",
        content_type=ContentType.IMAGE_PNG,
        filename="file.png",
        size_bytes=1024,
    )


def _job() -> AnalysisJob:
    return AnalysisJob(
        job_id=uuid4(),
        session_id=uuid4(),
        user_id=uuid4(),
        assets=(_asset(),),
        prompt_version="v1",
        submitted_at=datetime.now(UTC),
    )


def test_asset_is_frozen():
    a = _asset()
    with pytest.raises(FrozenInstanceError):
        a.filename = "other.png"  # type: ignore[misc]


def test_analysis_job_is_frozen_and_assets_is_tuple():
    j = _job()
    assert isinstance(j.assets, tuple)
    with pytest.raises(FrozenInstanceError):
        j.prompt_version = "v2"  # type: ignore[misc]


def test_structured_report_minimal_construction():
    r = StructuredReport(
        summary="hi",
        confidence=Confidence.HIGH,
        components=(
            Component(
                name="api",
                kind=ComponentKind.SERVICE,
                responsibility="x",
                relevance=Relevance.HIGH,
                evidence="diagram label",
            ),
        ),
        risks=(
            Risk(
                title="t",
                category=RiskCategory.SECURITY,
                severity=Severity.HIGH,
                description="d",
                affected_components=("api",),
                recommendation="r",
            ),
        ),
        improvements=(
            Improvement(
                title="t",
                rationale="r",
                impact=ImpactEffort.HIGH,
                effort=ImpactEffort.LOW,
                affected_components=("api",),
            ),
        ),
        strengths=(Strength(title="t", description="d"),),
        model_metadata=ModelMetadata(
            model="claude-sonnet-4-6",
            tokens_in=10,
            tokens_out=20,
            duration_ms=100,
        ),
    )
    assert r.confidence is Confidence.HIGH
    assert len(r.components) == 1


def test_status_enum_values():
    assert {s.value for s in AnalysisStatus} == {"STARTED", "SUCCEEDED", "FAILED"}


def test_domain_has_no_framework_imports():
    """Hex invariant: domain modules must not import frameworks."""
    forbidden = {"fastapi", "sqlalchemy", "boto3", "anthropic", "pydantic"}
    for name in ("smart_service.domain.model", "smart_service.domain.ports"):
        mod = importlib.import_module(name)
        src_path = mod.__file__ or ""
        with open(src_path) as fh:
            src = fh.read()
        for f in forbidden:
            assert f"import {f}" not in src, f"{name} imports {f}"
            assert f"from {f}" not in src, f"{name} imports from {f}"
