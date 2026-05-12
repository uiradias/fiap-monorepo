"""Unit tests for the scorer. Pure logic, no API calls - runs in the default suite."""
from __future__ import annotations

import pytest

from smart_service.domain.citation import Citation
from smart_service.domain.model import (
    Component,
    ComponentKind,
    Confidence,
    ModelMetadata,
    Relevance,
    Risk,
    RiskCategory,
    Severity,
    StructuredReport,
)
from tests.eval.scorer import EvalSpec, score


def _report(*, risks=(), components=()) -> StructuredReport:
    return StructuredReport(
        summary="s", confidence=Confidence.HIGH,
        components=components,
        risks=risks,
        improvements=(), strengths=(),
        model_metadata=ModelMetadata(model="m"),
    )


def _comp(name: str) -> Component:
    return Component(
        name=name, kind=ComponentKind.SERVICE, responsibility="r",
        relevance=Relevance.HIGH, evidence="e",
    )


def _risk(*, title="t", desc="d", sev=Severity.HIGH, citations=()) -> Risk:
    return Risk(
        title=title, category=RiskCategory.SECURITY, severity=sev,
        description=desc, affected_components=(), recommendation="r",
        citations=citations,
    )


def test_component_recall_perfect():
    spec = EvalSpec("a", ["Gateway", "Service A"], [], [])
    s = score(spec, _report(components=(_comp("API Gateway"), _comp("Service A"))))
    assert s.component_recall == 1.0


def test_component_recall_partial():
    spec = EvalSpec("a", ["X", "Y", "Z"], [], [])
    s = score(spec, _report(components=(_comp("X"),)))
    assert s.component_recall == pytest.approx(1 / 3)


def test_risk_recall_requires_keyword_and_citation_and_severity():
    spec = EvalSpec("a", [], [{
        "keywords_any": ["sync"], "citation_doc_ids_any": ["WA-REL-04"],
        "min_severity": "high",
    }], [])
    cit = Citation(doc_id="WA-REL-04", source="s", title="t",
                   chunk_index=0, score=0.9)
    # all match
    s_match = score(spec, _report(risks=(_risk(
        title="sync coupling", sev=Severity.HIGH, citations=(cit,),
    ),)))
    assert s_match.risk_recall == 1.0
    # missing keyword
    s_no_kw = score(spec, _report(risks=(_risk(
        title="other", sev=Severity.HIGH, citations=(cit,),
    ),)))
    assert s_no_kw.risk_recall == 0.0
    # missing citation
    s_no_cit = score(spec, _report(risks=(_risk(
        title="sync coupling", sev=Severity.HIGH,
    ),)))
    assert s_no_cit.risk_recall == 0.0
    # severity too low
    s_low_sev = score(spec, _report(risks=(_risk(
        title="sync coupling", sev=Severity.LOW, citations=(cit,),
    ),)))
    assert s_low_sev.risk_recall == 0.0


def test_citation_rate_counts_risks_with_at_least_one_citation():
    cit = Citation(doc_id="X", source="s", title="t", chunk_index=0, score=0.9)
    s = score(
        EvalSpec("a", [], [], []),
        _report(risks=(
            _risk(citations=(cit,)),
            _risk(citations=()),
            _risk(citations=(cit, cit)),
        )),
    )
    assert s.citation_rate == pytest.approx(2 / 3)


def test_hallucination_count_finds_forbidden_keywords():
    s = score(
        EvalSpec("a", [], [], ["Kafka", "Lambda"]),
        _report(risks=(
            _risk(title="uses kafka heavily"),
            _risk(title="ok"),
            _risk(title="lambda function"),
        )),
    )
    assert s.hallucination_count == 2  # Kafka + Lambda each found in one risk


def test_empty_report_yields_zero_recall():
    spec = EvalSpec("a", ["X"], [{"keywords_any": ["x"]}], ["y"])
    s = score(spec, _report())
    assert s.component_recall == 0.0
    assert s.risk_recall == 0.0
    assert s.citation_rate == 0.0
    assert s.hallucination_count == 0
