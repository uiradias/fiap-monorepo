"""Integration test against a real pgvector-enabled Postgres.

Vectors are padded to 1024 dims to match the production migration; the values
that matter for ordering live in the first few positions.
"""
from __future__ import annotations

import os
import subprocess

import pgvector.sqlalchemy  # noqa: F401  # registers `vector` in PG dialect ischema_names
import pytest
from sqlalchemy import create_engine, text
from testcontainers.postgres import PostgresContainer

from smart_service.adapter.outbound.pgvector_pattern_retriever import (
    PgVectorPatternRetriever,
)

pytestmark = pytest.mark.integration

EMBEDDING_DIM = 1024


def _pad(v: list[float]) -> list[float]:
    return v + [0.0] * (EMBEDDING_DIM - len(v))


@pytest.fixture(scope="module")
def migrated_engine():
    with PostgresContainer("pgvector/pgvector:pg16", driver="psycopg") as pg:
        url = pg.get_connection_url()
        env = {**os.environ, "SMART_DATABASE_URL": url}
        bootstrap = create_engine(url)
        with bootstrap.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        bootstrap.dispose()
        subprocess.run(
            ["uv", "run", "alembic", "upgrade", "head"],
            env=env, check=True, capture_output=True, text=True,
        )
        engine = create_engine(url)
        try:
            yield engine
        finally:
            engine.dispose()


def _seed(engine, rows):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM corpus_chunks"))
        conn.execute(text("DELETE FROM corpus_documents"))
        for r in rows:
            doc_id = conn.execute(text(
                "INSERT INTO corpus_documents (doc_id, source, title, category, version) "
                "VALUES (:d, :s, :t, :c, :v) RETURNING id"
            ), {"d": r["doc_id"], "s": r["source"], "t": r["title"],
                "c": r["category"], "v": "v1"}).scalar_one()
            conn.execute(text(
                "INSERT INTO corpus_chunks "
                "(document_id, chunk_index, content, applies_to, version, embedding) "
                "VALUES (:doc, 0, :content, :tags, 'v1', CAST(:emb AS vector))"
            ), {
                "doc": doc_id, "content": r["content"],
                "tags": r["applies_to"], "emb": str(_pad(r["embedding"])),
            })


def test_returns_topk_ordered_by_similarity(migrated_engine):
    _seed(migrated_engine, [
        {"doc_id": "A", "source": "x", "title": "A", "category": "c",
         "content": "queues are async", "applies_to": ["msg:queue"],
         "embedding": [1.0, 0.0, 0.0, 0.0]},
        {"doc_id": "B", "source": "x", "title": "B", "category": "c",
         "content": "http is sync", "applies_to": ["http:sync"],
         "embedding": [0.0, 1.0, 0.0, 0.0]},
        {"doc_id": "C", "source": "x", "title": "C", "category": "c",
         "content": "object store", "applies_to": ["storage:object"],
         "embedding": [0.0, 0.0, 1.0, 0.0]},
    ])
    retriever = PgVectorPatternRetriever(engine=migrated_engine, embedding_dim=EMBEDDING_DIM)
    out = retriever.search(
        query_embedding=_pad([0.9, 0.1, 0.0, 0.0]),
        applies_to_any=[],
        top_k=2,
    )
    assert [m.doc_id for m in out] == ["A", "B"]
    assert all(m.score > 0 for m in out)


def test_filters_by_applies_to(migrated_engine):
    _seed(migrated_engine, [
        {"doc_id": "A", "source": "x", "title": "A", "category": "c",
         "content": "queues", "applies_to": ["msg:queue"],
         "embedding": [1.0, 0.0, 0.0, 0.0]},
        {"doc_id": "B", "source": "x", "title": "B", "category": "c",
         "content": "http", "applies_to": ["http:sync"],
         "embedding": [1.0, 0.0, 0.0, 0.0]},  # tied with A on similarity
    ])
    retriever = PgVectorPatternRetriever(engine=migrated_engine, embedding_dim=EMBEDDING_DIM)
    out = retriever.search(
        query_embedding=_pad([1.0, 0.0, 0.0, 0.0]),
        applies_to_any=["http:sync"],
        top_k=5,
    )
    assert [m.doc_id for m in out] == ["B"]


def test_returns_empty_when_no_matches(migrated_engine):
    _seed(migrated_engine, [
        {"doc_id": "A", "source": "x", "title": "A", "category": "c",
         "content": "", "applies_to": ["msg:queue"],
         "embedding": [1.0, 0.0, 0.0, 0.0]},
    ])
    retriever = PgVectorPatternRetriever(engine=migrated_engine, embedding_dim=EMBEDDING_DIM)
    out = retriever.search(
        query_embedding=_pad([1.0, 0.0, 0.0, 0.0]),
        applies_to_any=["does-not-exist"],
        top_k=5,
    )
    assert out == []


def test_intersects_multiple_applies_to_tags(migrated_engine):
    _seed(migrated_engine, [
        {"doc_id": "A", "source": "x", "title": "A", "category": "c",
         "content": "queues", "applies_to": ["msg:queue"],
         "embedding": [1.0, 0.0, 0.0, 0.0]},
        {"doc_id": "B", "source": "x", "title": "B", "category": "c",
         "content": "http", "applies_to": ["http:sync"],
         "embedding": [1.0, 0.0, 0.0, 0.0]},
        {"doc_id": "C", "source": "x", "title": "C", "category": "c",
         "content": "other", "applies_to": ["db:relational"],
         "embedding": [1.0, 0.0, 0.0, 0.0]},
    ])
    retriever = PgVectorPatternRetriever(engine=migrated_engine, embedding_dim=EMBEDDING_DIM)
    out = retriever.search(
        query_embedding=_pad([1.0, 0.0, 0.0, 0.0]),
        applies_to_any=["msg:queue", "http:sync"],
        top_k=5,
    )
    assert {m.doc_id for m in out} == {"A", "B"}
    assert "C" not in {m.doc_id for m in out}


def test_rejects_wrong_dimension(migrated_engine):
    retriever = PgVectorPatternRetriever(engine=migrated_engine, embedding_dim=EMBEDDING_DIM)
    with pytest.raises(ValueError):
        retriever.search(
            query_embedding=[0.1, 0.2],  # wrong dim
            applies_to_any=[],
            top_k=3,
        )
