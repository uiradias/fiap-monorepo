"""Asserts the corpus tables exist after migrations run. Integration test."""
from __future__ import annotations

import os
import subprocess

import pgvector.sqlalchemy  # noqa: F401  # registers `vector` in PG dialect ischema_names
import pytest
from sqlalchemy import create_engine, inspect, text
from testcontainers.postgres import PostgresContainer

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def migrated_engine():
    with PostgresContainer("pgvector/pgvector:pg16", driver="psycopg") as pg:
        url = pg.get_connection_url()
        env = {**os.environ, "SMART_DATABASE_URL": url}
        # Install the extension as superuser before running migrations.
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


def test_corpus_documents_table_exists(migrated_engine):
    insp = inspect(migrated_engine)
    cols = {c["name"] for c in insp.get_columns("corpus_documents")}
    assert {"id", "doc_id", "source", "title", "category", "version", "created_at"} <= cols


def test_corpus_chunks_table_exists_with_vector_column(migrated_engine):
    insp = inspect(migrated_engine)
    cols = {c["name"] for c in insp.get_columns("corpus_chunks")}
    assert {"id", "document_id", "chunk_index", "content", "embedding",
            "applies_to", "version"} <= cols


def test_corpus_chunks_has_indexes(migrated_engine):
    with migrated_engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT indexname FROM pg_indexes WHERE tablename='corpus_chunks'"
        )).all()
    names = {r[0] for r in rows}
    assert any("hnsw" in n.lower() or "embedding" in n.lower() for n in names)
    assert any("applies_to" in n.lower() for n in names)
