"""Dense retrieval over corpus_chunks via pgvector cosine similarity."""
from __future__ import annotations

from sqlalchemy import Engine, text

from smart_service.domain.corpus import PatternMatch


class PgVectorPatternRetriever:
    """Dense-only retrieval. BM25 and rerank are out of scope for the minimal slice."""

    def __init__(self, *, engine: Engine, embedding_dim: int) -> None:
        self._engine = engine
        self._dim = embedding_dim

    def search(
        self,
        query_embedding: list[float],
        applies_to_any: list[str],
        top_k: int,
    ) -> list[PatternMatch]:
        if len(query_embedding) != self._dim:
            raise ValueError(
                f"embedding dim mismatch: got {len(query_embedding)}, expected {self._dim}"
            )
        sql = """
            SELECT d.doc_id, d.source, d.title, d.category,
                   c.chunk_index, c.content,
                   1.0 - (c.embedding <=> CAST(:q AS vector)) AS score
            FROM corpus_chunks c
            JOIN corpus_documents d ON d.id = c.document_id
            WHERE (:filter_off OR c.applies_to && CAST(:tags AS text[]))
            ORDER BY c.embedding <=> CAST(:q AS vector)
            LIMIT :k
        """
        params = {
            "q": str(query_embedding),
            "tags": applies_to_any,
            "filter_off": len(applies_to_any) == 0,
            "k": top_k,
        }
        with self._engine.connect() as conn:
            rows = conn.execute(text(sql), params).all()
        return [
            PatternMatch(
                doc_id=r[0], source=r[1], title=r[2], category=r[3],
                chunk_index=r[4], content=r[5], score=float(r[6]),
            )
            for r in rows
        ]
