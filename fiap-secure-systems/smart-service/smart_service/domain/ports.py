"""Outbound port Protocols. Adapters in `adapter/outbound/` implement these."""
from __future__ import annotations

from typing import Protocol
from uuid import UUID

from smart_service.domain.model import (
    AnalysisJob,
    AnalysisOutcome,
    Asset,
    StructuredReport,
)


class AssetReaderPort(Protocol):
    """Reads asset bytes from storage by key."""

    def read(self, asset: Asset) -> bytes: ...


class AnalysisModelPort(Protocol):
    """Runs the AI model on a job's assets and returns a structured report.

    Implementations must NOT publish messages, persist state, or do any I/O outside
    of the model call. Failure is signalled by raising `AnalysisModelError`.
    """

    def analyze(self, job: AnalysisJob, asset_bytes: dict[UUID, bytes]) -> StructuredReport: ...


class ResultPublisherPort(Protocol):
    """Publishes an AnalysisOutcome to the analysis-results SQS queue."""

    def publish(self, outcome: AnalysisOutcome) -> None: ...


class AuditRepositoryPort(Protocol):
    """Persists run state to smart_db.analysis_runs and inbound dedup to processed_jobs."""

    def is_already_processed(self, job_id: UUID) -> bool: ...
    def mark_processed(self, job_id: UUID) -> None: ...
    def start_run(self, job: AnalysisJob, model: str) -> None: ...
    def mark_succeeded(
        self,
        job_id: UUID,
        report: StructuredReport,
        duration_ms: int,
    ) -> None: ...
    def mark_failed(self, job_id: UUID, error: str, duration_ms: int) -> None: ...


class AnalysisModelError(Exception):
    """Raised by AnalysisModelPort.analyze on any non-recoverable model failure.

    The application service catches this, marks the run FAILED, and publishes a
    FAILED AnalysisResult. Retryable errors (429/5xx) should be handled inside the
    adapter via its own retry policy before raising.
    """

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


class EmbeddingPort(Protocol):
    """Embeds a batch of text strings into fixed-dimension vectors.

    Returns a list of float lists in the same order as the input. Implementations
    must surface API failures as EmbeddingError; the caller decides retry policy.
    """

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class EmbeddingError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


from smart_service.domain.corpus import PatternMatch  # noqa: E402


class PatternRetrievalPort(Protocol):
    """Retrieves corpus chunks relevant to a query embedding.

    `applies_to_any` filters chunks whose `applies_to` array intersects the given
    tags. An empty list disables the filter (topology-level queries). `top_k` caps
    results. Results are ordered by similarity (highest first).
    """

    def search(
        self,
        query_embedding: list[float],
        applies_to_any: list[str],
        top_k: int,
    ) -> list[PatternMatch]: ...


from smart_service.domain.graph import ComponentGraph  # noqa: E402


class ComponentExtractorPort(Protocol):
    """Extracts a ComponentGraph from image/PDF bytes.

    Input is a list of (media_type, bytes) pairs — one per asset in the job.
    Implementations MAY call out to a vision model. Failures surface as
    AnalysisModelError (callers already handle that error type).
    """

    def extract(self, asset_bytes: list[tuple[str, bytes]]) -> ComponentGraph: ...


class CanonicalizerPort(Protocol):
    """Refines a ComponentGraph by re-classifying UNKNOWN components.

    Implementations MAY return the input graph unchanged. Implementations MUST
    NOT alter edges or node_ids — only `kind` on components. Returning the input
    on any API failure is acceptable (best-effort refinement).
    """

    def canonicalize(self, graph: ComponentGraph) -> ComponentGraph: ...
