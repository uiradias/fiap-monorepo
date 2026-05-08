"""Deterministic AnalysisModelPort for offline runs (SMART_SERVICE_PROFILE=e2e) and tests."""
from __future__ import annotations

from uuid import UUID

from smart_service.domain.model import (
    AnalysisJob,
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


class FakeAnalysisModel:
    """Always returns the same minimal-but-valid report. No I/O."""

    def __init__(self, *, model_id: str = "fake-claude") -> None:
        self._model_id = model_id

    def analyze(
        self,
        job: AnalysisJob,
        asset_bytes: dict[UUID, bytes],
    ) -> StructuredReport:
        del asset_bytes  # kept for port conformance; fake model ignores bytes
        first_asset = job.assets[0]
        return StructuredReport(
            summary=(
                f"(fake) Architecture review of {len(job.assets)} asset(s); "
                f"first asset filename={first_asset.filename}."
            ),
            confidence=Confidence.LOW,
            components=(
                Component(
                    name="ingest",
                    kind=ComponentKind.SERVICE,
                    responsibility="(fake) accepts assets",
                    relevance=Relevance.HIGH,
                    evidence=f"(fake) inferred from filename {first_asset.filename}",
                ),
            ),
            risks=(
                Risk(
                    title="(fake) example risk",
                    category=RiskCategory.OPERABILITY,
                    severity=Severity.LOW,
                    description="placeholder risk for e2e profile",
                    affected_components=("ingest",),
                    recommendation="run with the production profile to get a real review",
                ),
            ),
            improvements=(
                Improvement(
                    title="(fake) example improvement",
                    rationale="placeholder improvement",
                    impact=ImpactEffort.LOW,
                    effort=ImpactEffort.LOW,
                    affected_components=("ingest",),
                ),
            ),
            strengths=(
                Strength(title="(fake) deterministic", description="reproducible offline output"),
            ),
            model_metadata=ModelMetadata(
                model=self._model_id, tokens_in=0, tokens_out=0, duration_ms=1
            ),
        )
