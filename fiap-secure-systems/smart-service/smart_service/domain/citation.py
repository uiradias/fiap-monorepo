"""Citation — a pointer back to a corpus chunk that grounds a risk."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Citation:
    doc_id: str
    source: str
    title: str
    chunk_index: int
    score: float
