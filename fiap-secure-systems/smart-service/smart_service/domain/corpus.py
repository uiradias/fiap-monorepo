"""Corpus value types — what gets ingested and what retrieval returns."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CorpusChunk:
    chunk_index: int
    content: str
    applies_to: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CorpusDocument:
    doc_id: str
    source: str
    title: str
    category: str
    version: str
    chunks: tuple[CorpusChunk, ...]


@dataclass(frozen=True, slots=True)
class PatternMatch:
    """A single retrieval result returned to the analysis pipeline."""

    doc_id: str
    source: str
    title: str
    category: str
    chunk_index: int
    content: str
    score: float
