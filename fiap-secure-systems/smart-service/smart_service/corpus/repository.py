"""Upsert corpus documents and their (re-embedded) chunks atomically."""
from __future__ import annotations

from sqlalchemy import Engine, text

from smart_service.domain.corpus import CorpusDocument


class PostgresCorpusRepository:
    def __init__(self, *, engine: Engine) -> None:
        self._engine = engine

    def upsert(self, doc: CorpusDocument, embeddings: list[list[float]]) -> int:
        if len(embeddings) != len(doc.chunks):
            raise ValueError("embeddings length must match chunks length")
        with self._engine.begin() as conn:
            # Delete existing document by doc_id (CASCADE wipes chunks via FK).
            conn.execute(
                text("DELETE FROM corpus_documents WHERE doc_id = :d"),
                {"d": doc.doc_id},
            )
            new_id = conn.execute(text(
                "INSERT INTO corpus_documents (doc_id, source, title, category, version) "
                "VALUES (:d, :s, :t, :c, :v) RETURNING id"
            ), {"d": doc.doc_id, "s": doc.source, "t": doc.title,
                "c": doc.category, "v": doc.version}).scalar_one()
            for chunk, emb in zip(doc.chunks, embeddings, strict=True):
                conn.execute(text(
                    "INSERT INTO corpus_chunks "
                    "(document_id, chunk_index, content, applies_to, version, embedding) "
                    "VALUES (:doc, :i, :content, :tags, :v, CAST(:emb AS vector))"
                ), {
                    "doc": new_id, "i": chunk.chunk_index, "content": chunk.content,
                    "tags": list(chunk.applies_to), "v": doc.version, "emb": str(emb),
                })
        return len(doc.chunks)
