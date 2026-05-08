"""Pydantic model matching the AI-output JSON schema.

Source schema: `infrastructure/contracts/analysis-report.schema.json`.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ComponentModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    kind: Literal[
        "service", "datastore", "queue", "gateway", "client", "external", "other"
    ]
    responsibility: str = Field(min_length=1)
    relevance: Literal["high", "medium", "low"]
    evidence: str = Field(min_length=1)


class RiskModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)
    category: Literal[
        "security", "scalability", "availability", "cost", "operability", "data", "compliance"
    ]
    severity: Literal["critical", "high", "medium", "low"]
    description: str = Field(min_length=1)
    affected_components: list[str] = Field(default_factory=list)
    recommendation: str = Field(min_length=1)


class ImprovementModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    impact: Literal["high", "medium", "low"]
    effort: Literal["high", "medium", "low"]
    affected_components: list[str] = Field(default_factory=list)


class StrengthModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)
    description: str = Field(min_length=1)


class ReportModelMetadata(BaseModel):
    # protected_namespaces=() — silence Pydantic v2 warning on the `model` field name.
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    model: str = Field(min_length=1)
    tokens_in: int = Field(default=0, ge=0)
    tokens_out: int = Field(default=0, ge=0)
    duration_ms: int = Field(default=0, ge=0)


class StructuredReportModel(BaseModel):
    # protected_namespaces=() — silence Pydantic v2 warning on the `model_metadata` field name.
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    summary: str = Field(min_length=1, max_length=1000)
    components: list[ComponentModel] = Field(default_factory=list)
    risks: list[RiskModel] = Field(default_factory=list)
    improvements: list[ImprovementModel] = Field(default_factory=list)
    strengths: list[StrengthModel] = Field(default_factory=list)
    confidence: Literal["high", "medium", "low"]
    model_metadata: ReportModelMetadata
