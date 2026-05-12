"""Scoring helpers for the eval harness. Pure functions over StructuredReport."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_service.domain.model import StructuredReport


@dataclass(frozen=True, slots=True)
class EvalSpec:
    architecture_id: str
    expected_components: list[str]
    must_find_risks: list[dict[str, Any]]
    forbidden_keywords: list[str]


@dataclass(frozen=True, slots=True)
class EvalScore:
    architecture_id: str
    component_recall: float
    risk_recall: float
    citation_rate: float
    hallucination_count: int


_SEV_RANK = {"low": 1, "medium": 2, "high": 3, "critical": 4}


def score(spec: EvalSpec, report: StructuredReport) -> EvalScore:
    report_comp_names = [c.name.lower() for c in report.components]
    expected = [e.lower() for e in spec.expected_components]
    hits = 0
    for e in expected:
        if any(e in name or name in e for name in report_comp_names):
            hits += 1
    comp_recall = hits / max(1, len(expected))

    risks_found = 0
    for must in spec.must_find_risks:
        kw_any = [k.lower() for k in must.get("keywords_any", [])]
        cit_any = set(must.get("citation_doc_ids_any", []))
        min_sev = must.get("min_severity", "low")
        threshold = _SEV_RANK.get(min_sev, 0)
        for r in report.risks:
            text = f"{r.title} {r.description} {r.recommendation}".lower()
            kw_ok = any(k in text for k in kw_any) if kw_any else True
            cit_ok = (
                any(c.doc_id in cit_any for c in r.citations) if cit_any else True
            )
            sev_ok = _SEV_RANK.get(r.severity.value, 0) >= threshold
            if kw_ok and cit_ok and sev_ok:
                risks_found += 1
                break
    risk_recall = risks_found / max(1, len(spec.must_find_risks))

    cited = sum(1 for r in report.risks if r.citations)
    citation_rate = cited / max(1, len(report.risks))

    hallucinations = 0
    for kw in spec.forbidden_keywords:
        kw_l = kw.lower()
        for r in report.risks:
            if kw_l in f"{r.title} {r.description}".lower():
                hallucinations += 1
                break

    return EvalScore(
        architecture_id=spec.architecture_id,
        component_recall=comp_recall,
        risk_recall=risk_recall,
        citation_rate=citation_rate,
        hallucination_count=hallucinations,
    )
