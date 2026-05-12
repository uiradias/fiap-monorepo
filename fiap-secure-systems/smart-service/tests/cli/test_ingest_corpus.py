"""Integration test: ingest YAML files into pgvector and confirm idempotency."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pgvector.sqlalchemy  # noqa: F401  # registers `vector` in PG dialect ischema_names
import pytest
from sqlalchemy import create_engine, text
from testcontainers.postgres import PostgresContainer

from smart_service.cli.ingest_corpus import ingest

pytestmark = pytest.mark.integration

EMBEDDING_DIM = 1024


class _StaticEmbedder:
    """Embedder returning a deterministic vector per text. 1024-dim, mostly zero."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vec(t) for t in texts]

    def embed_query(self, texts: list[str]) -> list[list[float]]:
        return [self._vec(t) for t in texts]

    def _vec(self, t: str) -> list[float]:
        seed = sum(ord(c) for c in t) % 7 + 1
        v = [0.0] * EMBEDDING_DIM
        v[0] = float(seed)
        return v


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


def _write_yaml(path: Path, doc_id: str, n_chunks: int) -> None:
    path.write_text(
        f"doc_id: {doc_id}\nsource: test\ntitle: t\ncategory: c\n"
        f"version: v1\nchunks:\n"
        + "".join(
            f"  - applies_to: [msg:queue]\n    content: chunk-{i}\n"
            for i in range(n_chunks)
        )
    )


def _clear(engine):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM corpus_chunks"))
        conn.execute(text("DELETE FROM corpus_documents"))


def test_ingest_inserts_documents_and_chunks(migrated_engine, tmp_path):
    _clear(migrated_engine)
    _write_yaml(tmp_path / "a.yaml", "A", 2)
    _write_yaml(tmp_path / "b.yaml", "B", 1)
    embedder = _StaticEmbedder()
    n = ingest(corpus_dir=tmp_path, engine=migrated_engine, embedder=embedder)
    assert n == 3
    with migrated_engine.connect() as conn:
        docs = conn.execute(text("SELECT doc_id FROM corpus_documents ORDER BY doc_id")).all()
        chunks = conn.execute(text("SELECT COUNT(*) FROM corpus_chunks")).scalar_one()
    assert [r[0] for r in docs] == ["A", "B"]
    assert chunks == 3


def test_ingest_is_idempotent_on_doc_id(migrated_engine, tmp_path):
    _clear(migrated_engine)
    _write_yaml(tmp_path / "a.yaml", "A", 2)
    embedder = _StaticEmbedder()
    ingest(corpus_dir=tmp_path, engine=migrated_engine, embedder=embedder)
    ingest(corpus_dir=tmp_path, engine=migrated_engine, embedder=embedder)
    with migrated_engine.connect() as conn:
        docs = conn.execute(
            text("SELECT COUNT(*) FROM corpus_documents WHERE doc_id='A'")
        ).scalar_one()
        chunks = conn.execute(text("SELECT COUNT(*) FROM corpus_chunks")).scalar_one()
    assert docs == 1
    assert chunks == 2  # not duplicated


def test_ingest_replaces_chunks_when_yaml_changes(migrated_engine, tmp_path):
    """Re-ingesting a doc with FEWER chunks must reduce the chunk count."""
    _clear(migrated_engine)
    _write_yaml(tmp_path / "a.yaml", "A", 3)
    ingest(corpus_dir=tmp_path, engine=migrated_engine, embedder=_StaticEmbedder())
    _write_yaml(tmp_path / "a.yaml", "A", 1)
    ingest(corpus_dir=tmp_path, engine=migrated_engine, embedder=_StaticEmbedder())
    with migrated_engine.connect() as conn:
        chunks = conn.execute(text("SELECT COUNT(*) FROM corpus_chunks")).scalar_one()
    assert chunks == 1


def test_ingest_skips_non_yaml_files(migrated_engine, tmp_path):
    _clear(migrated_engine)
    _write_yaml(tmp_path / "a.yaml", "A", 1)
    (tmp_path / "readme.md").write_text("# notes\n")
    (tmp_path / "other.json").write_text("{}")
    n = ingest(corpus_dir=tmp_path, engine=migrated_engine, embedder=_StaticEmbedder())
    assert n == 1
