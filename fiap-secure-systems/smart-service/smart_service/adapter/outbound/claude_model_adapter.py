"""Anthropic Claude adapter with prompt caching. Implements AnalysisModelPort."""
from __future__ import annotations

import base64
import json
import re
import time
from pathlib import Path
from typing import Any
from uuid import UUID

import anthropic

from smart_service.adapter.schema.validation import (
    SchemaValidationError,
    validate_analysis_report,
)
from smart_service.infrastructure.metrics import record_anthropic_call_duration_ms
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
from smart_service.domain.ports import AnalysisModelError

SYSTEM_PROMPT = """You are an expert system-architecture reviewer.

You will be given one or more architecture diagrams (images and/or PDFs). Produce a
structured architecture review as a SINGLE JSON object that conforms EXACTLY to the
JSON Schema below — no prose, no markdown, no preamble, no comments. Output only
the JSON object.

Required output keys: summary, components, risks, improvements, strengths,
confidence, model_metadata. The `model_metadata` object you produce only needs the
`model` field; tokens and duration are filled in by the runtime.

Guidance:
- `summary`: 2-3 sentence executive summary.
- `components`: every distinct architectural element shown in the diagrams.
- `risks`: prioritized concerns; reference component names in `affected_components`.
- `improvements`: actionable suggestions with realistic impact/effort tradeoffs.
- `strengths`: positive aspects worth keeping.
- `confidence`: your overall confidence in the review given image quality and detail.

JSON Schema (authoritative):
"""


class ClaudeModelAdapter:
    def __init__(
        self,
        *,
        client: anthropic.Anthropic,
        model: str,
        contracts_dir: Path,
    ) -> None:
        self._client = client
        self._model = model
        self._contracts_dir = contracts_dir
        self._report_schema_text = (
            contracts_dir / "analysis-report.schema.json"
        ).read_text()

    def analyze(
        self,
        job: AnalysisJob,
        asset_bytes: dict[UUID, bytes],
    ) -> StructuredReport:
        system_text = SYSTEM_PROMPT + self._report_schema_text
        user_blocks: list[dict[str, Any]] = [
            {
                "type": "text",
                "text": (
                    f"Job {job.job_id} — session {job.session_id}. "
                    f"{len(job.assets)} asset(s) attached. Produce the JSON object now."
                ),
            }
        ]
        for asset in job.assets:
            data = asset_bytes[asset.asset_id]
            b64 = base64.b64encode(data).decode("ascii")
            if asset.content_type.value == "application/pdf":
                user_blocks.append({
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": b64,
                    },
                })
            else:
                user_blocks.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": asset.content_type.value,
                        "data": b64,
                    },
                })

        started = time.monotonic()
        status = "ok"
        try:
            resp = self._client.messages.create(
                model=self._model,
                max_tokens=8192,
                system=[
                    {
                        "type": "text",
                        "text": system_text,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[{"role": "user", "content": user_blocks}],  # type: ignore[typeddict-item]
            )
        except anthropic.APIStatusError as e:
            code = "MODEL_RATE_LIMITED" if e.status_code == 429 else "MODEL_API_ERROR"
            status = "rate_limited" if e.status_code == 429 else "error"
            raise AnalysisModelError(code, str(e)) from e
        except anthropic.APIError as e:
            status = "error"
            raise AnalysisModelError("MODEL_API_ERROR", str(e)) from e
        finally:
            record_anthropic_call_duration_ms(
                (time.monotonic() - started) * 1000, self._model, status
            )

        elapsed_ms = int((time.monotonic() - started) * 1000)
        text = _extract_text(resp)
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as e:
            raise AnalysisModelError("MODEL_OUTPUT_INVALID", f"non-JSON response: {e}") from e

        try:
            validate_analysis_report(payload, self._contracts_dir)
        except SchemaValidationError as e:
            raise AnalysisModelError("MODEL_OUTPUT_INVALID", str(e)) from e

        try:
            return _payload_to_domain(
                payload,
                tokens_in=getattr(resp.usage, "input_tokens", 0) or 0,
                tokens_out=getattr(resp.usage, "output_tokens", 0) or 0,
                duration_ms=elapsed_ms,
                model=resp.model or self._model,
            )
        except (KeyError, ValueError) as e:
            raise AnalysisModelError("MODEL_OUTPUT_INVALID", str(e)) from e


# Models routinely wrap JSON in ```json ... ``` despite a system-prompt "no markdown"
# instruction. Strip the fence so json.loads doesn't bomb on the leading backtick.
_FENCE_RE = re.compile(r"\A```(?:[a-zA-Z]+)?\s*\n?(.*?)\n?```\Z", re.DOTALL)


def _extract_text(response: Any) -> str:
    parts = [b.text for b in response.content if getattr(b, "type", None) == "text"]
    text = "".join(parts).strip()
    m = _FENCE_RE.match(text)
    if m:
        text = m.group(1).strip()
    return text


def _payload_to_domain(
    p: dict[str, Any],
    *,
    tokens_in: int,
    tokens_out: int,
    duration_ms: int,
    model: str,
) -> StructuredReport:
    return StructuredReport(
        summary=p["summary"],
        confidence=Confidence(p["confidence"]),
        components=tuple(
            Component(
                name=c["name"],
                kind=ComponentKind(c["kind"]),
                responsibility=c["responsibility"],
                relevance=Relevance(c["relevance"]),
                evidence=c["evidence"],
            )
            for c in p["components"]
        ),
        risks=tuple(
            Risk(
                title=r["title"],
                category=RiskCategory(r["category"]),
                severity=Severity(r["severity"]),
                description=r["description"],
                affected_components=tuple(r.get("affected_components", [])),
                recommendation=r["recommendation"],
            )
            for r in p["risks"]
        ),
        improvements=tuple(
            Improvement(
                title=i["title"],
                rationale=i["rationale"],
                impact=ImpactEffort(i["impact"]),
                effort=ImpactEffort(i["effort"]),
                affected_components=tuple(i.get("affected_components", [])),
            )
            for i in p["improvements"]
        ),
        strengths=tuple(
            Strength(title=s["title"], description=s["description"]) for s in p["strengths"]
        ),
        model_metadata=ModelMetadata(
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            duration_ms=duration_ms,
        ),
    )
