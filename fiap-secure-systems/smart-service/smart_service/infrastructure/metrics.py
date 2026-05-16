"""Application-level OpenTelemetry metrics for smart-service."""
from __future__ import annotations

from opentelemetry import metrics
from opentelemetry.metrics import Histogram

_anthropic_call_duration_ms: Histogram | None = None


def _histogram() -> Histogram:
    global _anthropic_call_duration_ms
    if _anthropic_call_duration_ms is None:
        meter = metrics.get_meter("smart-service.app", "0.1.0")
        _anthropic_call_duration_ms = meter.create_histogram(
            "anthropic_call_duration_ms",
            unit="ms",
            description="Wall-clock latency of Anthropic messages.create calls",
            explicit_bucket_boundaries_advisory=[
                10, 50, 100, 250, 500, 1000, 2500, 5000, 10000, 30000, 60000,
            ],
        )
    return _anthropic_call_duration_ms


def record_anthropic_call_duration_ms(duration_ms: float, model: str, status: str) -> None:
    _histogram().record(duration_ms, {"model": model, "status": status})
