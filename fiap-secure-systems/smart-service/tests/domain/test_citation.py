from __future__ import annotations

from smart_service.domain.citation import Citation
from smart_service.domain.model import Risk, RiskCategory, Severity


def test_risk_defaults_to_empty_citations():
    r = Risk(
        title="t", category=RiskCategory.SECURITY, severity=Severity.HIGH,
        description="d", affected_components=("a",), recommendation="r",
    )
    assert r.citations == ()


def test_risk_accepts_citations():
    cit = Citation(doc_id="X", source="src", title="t", chunk_index=0, score=0.9)
    r = Risk(
        title="t", category=RiskCategory.SECURITY, severity=Severity.HIGH,
        description="d", affected_components=("a",), recommendation="r",
        citations=(cit,),
    )
    assert r.citations[0].doc_id == "X"


def test_citation_is_frozen_and_slotted():
    cit = Citation(doc_id="X", source="src", title="t", chunk_index=0, score=0.9)
    import dataclasses
    assert dataclasses.is_dataclass(cit)
    # frozen: AttributeError on mutation
    import pytest
    with pytest.raises(dataclasses.FrozenInstanceError):
        cit.score = 0.5  # type: ignore[misc]
