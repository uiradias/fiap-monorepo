"""YAML → CorpusDocument parser. Raises ValueError on missing/invalid fields."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from smart_service.domain.corpus import CorpusChunk, CorpusDocument

_REQUIRED_DOC = ("doc_id", "source", "title", "category", "version", "chunks")


def load_corpus_yaml(path: Path) -> CorpusDocument:
    raw: Any = yaml.safe_load(path.read_text())
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: expected a mapping at top level")
    missing = [k for k in _REQUIRED_DOC if k not in raw]
    if missing:
        raise ValueError(f"{path}: missing required fields: {missing}")
    chunks_raw = raw["chunks"]
    if not isinstance(chunks_raw, list) or not chunks_raw:
        raise ValueError(f"{path}: chunks must be a non-empty list")
    chunks = tuple(
        CorpusChunk(
            chunk_index=i,
            content=str(c["content"]).strip(),
            applies_to=tuple(str(x) for x in c.get("applies_to", [])),
        )
        for i, c in enumerate(chunks_raw)
    )
    return CorpusDocument(
        doc_id=str(raw["doc_id"]),
        source=str(raw["source"]),
        title=str(raw["title"]),
        category=str(raw["category"]),
        version=str(raw["version"]),
        chunks=chunks,
    )
