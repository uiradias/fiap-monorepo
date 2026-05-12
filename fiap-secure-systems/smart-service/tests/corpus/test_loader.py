from __future__ import annotations

from pathlib import Path

import pytest

from smart_service.corpus.loader import load_corpus_yaml
from smart_service.domain.corpus import CorpusDocument

FIXTURE = Path(__file__).parent / "fixtures" / "sample.yaml"


def test_loads_doc_metadata():
    doc = load_corpus_yaml(FIXTURE)
    assert isinstance(doc, CorpusDocument)
    assert doc.doc_id == "WA-REL-04"
    assert doc.source == "aws-well-architected"
    assert doc.category == "reliability"
    assert doc.version == "2026.05"


def test_loads_chunks_with_applies_to():
    doc = load_corpus_yaml(FIXTURE)
    assert len(doc.chunks) == 2
    assert doc.chunks[0].applies_to == ("msg:queue", "msg:topic", "msg:stream")
    assert doc.chunks[0].chunk_index == 0
    assert doc.chunks[1].chunk_index == 1
    assert "circuit breakers" in doc.chunks[1].content


def test_rejects_missing_required_field(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("doc_id: X\nsource: s\ntitle: t\n")  # missing category, version, chunks
    with pytest.raises(ValueError):
        load_corpus_yaml(bad)


def test_rejects_non_mapping_top_level(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("- just a list\n")
    with pytest.raises(ValueError):
        load_corpus_yaml(bad)


def test_rejects_empty_chunks_list(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        "doc_id: X\nsource: s\ntitle: t\ncategory: c\nversion: v\nchunks: []\n"
    )
    with pytest.raises(ValueError):
        load_corpus_yaml(bad)
