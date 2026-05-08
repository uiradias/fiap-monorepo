"""Pydantic models matching `infrastructure/contracts/analysis-{jobs,results}.schema.json`."""
# ruff: noqa: N815  field names mirror the JSON wire format (camelCase by spec)
from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from smart_service.adapter.schema.report import StructuredReportModel


class AssetMessage(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    assetId: UUID
    s3Key: str = Field(min_length=1)
    contentType: Literal["application/pdf", "image/png", "image/jpeg", "image/webp"]
    filename: str = Field(min_length=1)
    sizeBytes: int = Field(ge=1, le=26_214_400)


class AnalysisJobMessage(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schemaVersion: Literal[1]
    jobId: UUID
    sessionId: UUID
    userId: UUID
    assets: list[AssetMessage] = Field(min_length=1, max_length=20)
    promptVersion: str = Field(pattern=r"^v\d+$")
    submittedAt: datetime


class ErrorPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1)
    message: str = Field(min_length=1)


class ModelMetadataMessage(BaseModel):
    # protected_namespaces=() — silence Pydantic v2 warning on the `model` field name.
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    model: str = Field(min_length=1)
    tokensIn: int = Field(default=0, ge=0)
    tokensOut: int = Field(default=0, ge=0)
    durationMs: int = Field(default=0, ge=0)


class AnalysisResultMessage(BaseModel):
    """Outbound message; matches contracts/analysis-results.schema.json.

    Conditional requirements from the JSON schema (e.g. SUCCEEDED requires `result`)
    are enforced via the `validate_analysis_result()` helper, not here, so that
    intermediate construction (e.g. building a STARTED message) stays simple.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schemaVersion: Literal[1] = 1
    jobId: UUID
    sessionId: UUID
    status: Literal["STARTED", "SUCCEEDED", "FAILED"]
    result: StructuredReportModel | None = None
    error: ErrorPayload | None = None
    modelMetadata: ModelMetadataMessage | None = None
    completedAt: datetime
