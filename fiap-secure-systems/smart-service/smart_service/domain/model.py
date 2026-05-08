"""Pure domain types. No framework imports.

These types match the contracts in `infrastructure/contracts/*.schema.json` but are
not bound to any serialization library — adapters translate between domain and JSON.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class ContentType(StrEnum):
    APPLICATION_PDF = "application/pdf"
    IMAGE_PNG = "image/png"
    IMAGE_JPEG = "image/jpeg"
    IMAGE_WEBP = "image/webp"


class AnalysisStatus(StrEnum):
    STARTED = "STARTED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class Confidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Relevance(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ComponentKind(StrEnum):
    SERVICE = "service"
    DATASTORE = "datastore"
    QUEUE = "queue"
    GATEWAY = "gateway"
    CLIENT = "client"
    EXTERNAL = "external"
    OTHER = "other"


class RiskCategory(StrEnum):
    SECURITY = "security"
    SCALABILITY = "scalability"
    AVAILABILITY = "availability"
    COST = "cost"
    OPERABILITY = "operability"
    DATA = "data"
    COMPLIANCE = "compliance"


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ImpactEffort(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True, slots=True)
class Asset:
    asset_id: UUID
    s3_key: str
    content_type: ContentType
    filename: str
    size_bytes: int


@dataclass(frozen=True, slots=True)
class AnalysisJob:
    job_id: UUID
    session_id: UUID
    user_id: UUID
    assets: tuple[Asset, ...]
    prompt_version: str
    submitted_at: datetime


@dataclass(frozen=True, slots=True)
class Component:
    name: str
    kind: ComponentKind
    responsibility: str
    relevance: Relevance
    evidence: str


@dataclass(frozen=True, slots=True)
class Risk:
    title: str
    category: RiskCategory
    severity: Severity
    description: str
    affected_components: tuple[str, ...]
    recommendation: str


@dataclass(frozen=True, slots=True)
class Improvement:
    title: str
    rationale: str
    impact: ImpactEffort
    effort: ImpactEffort
    affected_components: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Strength:
    title: str
    description: str


@dataclass(frozen=True, slots=True)
class ModelMetadata:
    model: str
    tokens_in: int = 0
    tokens_out: int = 0
    duration_ms: int = 0


@dataclass(frozen=True, slots=True)
class StructuredReport:
    summary: str
    confidence: Confidence
    components: tuple[Component, ...]
    risks: tuple[Risk, ...]
    improvements: tuple[Improvement, ...]
    strengths: tuple[Strength, ...]
    model_metadata: ModelMetadata


@dataclass(frozen=True, slots=True)
class AnalysisFailure:
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class AnalysisOutcome:
    """Result of running the model: either a report (success) or a failure."""

    job_id: UUID
    session_id: UUID
    status: AnalysisStatus
    completed_at: datetime
    report: StructuredReport | None = None
    failure: AnalysisFailure | None = None
    model_metadata: ModelMetadata | None = field(default=None)
