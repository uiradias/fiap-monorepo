"""End-to-end round trip: ingest corpus, run GroundedAnalysisAdapter with stubbed
Anthropic + Voyage, assert a grounded report is produced.

Integration test — depends on Testcontainers Postgres. The Anthropic and Voyage
calls are stubbed so the test does not hit external APIs (those are covered by
the eval suite).
"""
from __future__ import annotations

import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pgvector.sqlalchemy  # noqa: F401  # registers `vector` in PG dialect ischema_names
import pytest
from sqlalchemy import create_engine, text
from testcontainers.postgres import PostgresContainer

from smart_service.adapter.outbound.grounded_analysis_adapter import (
    GroundedAnalysisAdapter,
)
from smart_service.adapter.outbound.pgvector_pattern_retriever import (
    PgVectorPatternRetriever,
)
from smart_service.cli.ingest_corpus import ingest
from smart_service.domain.model import AnalysisJob, Asset, ContentType

pytestmark = pytest.mark.integration

FIXTURES = Path(__file__).parents[1] / "fixtures" / "grounded"


class _ConstantEmbedder:
    """Embedder returning a deterministic 1024-dim vector for any input."""

    def embed(self, texts):
        return [[1.0] + [0.0] * 1023 for _ in texts]

    def embed_query(self, texts):
        return [[1.0] + [0.0] * 1023 for _ in texts]


class _GraphExtractor:
    """Returns a fixed 2-node graph regardless of input."""

    def extract(self, _):
        from smart_service.domain.graph import (
            CanonicalKind,
            ComponentGraph,
            EdgeProtocol,
            GraphComponent,
            GraphEdge,
        )
        return ComponentGraph(
            components=(
                GraphComponent("n1", "Gateway", CanonicalKind.NET_GATEWAY),
                GraphComponent("n2", "Service A", CanonicalKind.COMPUTE_CONTAINER),
            ),
            edges=(GraphEdge("n1", "n2", EdgeProtocol.HTTP_SYNC, ""),),
        )


class _Passthrough:
    def canonicalize(self, g):
        return g


def _emit_client():
    fixture = json.loads((FIXTURES / "emit_tool_use_response.json").read_text())

    class _C:
        messages = SimpleNamespace(create=lambda **kw: SimpleNamespace(
            id=fixture["id"], model=fixture["model"],
            stop_reason=fixture["stop_reason"],
            usage=SimpleNamespace(**fixture["usage"]),
            content=[SimpleNamespace(**b) for b in fixture["content"]],
        ))

    return _C()


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


def test_round_trip_with_seeded_corpus(migrated_engine, tmp_path):
    # Seed a minimal corpus with one entry that the emit fixture cites.
    yaml_path = tmp_path / "WA-REL-04-sync-coupling.yaml"
    yaml_path.write_text(
        "doc_id: WA-REL-04-sync-coupling\n"
        "source: aws-well-architected\n"
        "title: Sync coupling\n"
        "category: reliability\n"
        "version: v1\n"
        "chunks:\n"
        "  - applies_to: [http:sync, net:gateway, compute:container]\n"
        "    content: Sync chains amplify failure.\n"
    )
    ingest(corpus_dir=tmp_path, engine=migrated_engine, embedder=_ConstantEmbedder())

    adapter = GroundedAnalysisAdapter(
        extractor=_GraphExtractor(),
        canonicalizer=_Passthrough(),
        embedder=_ConstantEmbedder(),
        retriever=PgVectorPatternRetriever(engine=migrated_engine, embedding_dim=1024),
        anthropic_client=_emit_client(),
        model="claude-sonnet-4-6",
    )

    asset = Asset(
        asset_id=uuid4(), s3_key="x",
        content_type=ContentType.IMAGE_PNG, filename="x.png", size_bytes=1,
    )
    job = AnalysisJob(
        job_id=uuid4(), session_id=uuid4(), user_id=uuid4(),
        assets=(asset,), prompt_version="v1", submitted_at=datetime.now(UTC),
    )
    report = adapter.analyze(job, {asset.asset_id: b"x"})

    # The emit fixture cites WA-REL-04-sync-coupling#0; with that doc seeded in
    # the corpus, the citation resolves and the cited risk survives.
    assert any(r.citations for r in report.risks)
    cited_doc_ids = {c.doc_id for r in report.risks for c in r.citations}
    assert "WA-REL-04-sync-coupling" in cited_doc_ids


def test_round_trip_drops_risks_when_corpus_is_empty(migrated_engine, tmp_path):
    """No corpus → every risk citation is phantom → hallucination filter drops all."""
    # Don't ingest anything. Re-clear the table just in case.
    with migrated_engine.begin() as conn:
        conn.execute(text("DELETE FROM corpus_chunks"))
        conn.execute(text("DELETE FROM corpus_documents"))

    adapter = GroundedAnalysisAdapter(
        extractor=_GraphExtractor(),
        canonicalizer=_Passthrough(),
        embedder=_ConstantEmbedder(),
        retriever=PgVectorPatternRetriever(engine=migrated_engine, embedding_dim=1024),
        anthropic_client=_emit_client(),
        model="claude-sonnet-4-6",
    )

    asset = Asset(
        asset_id=uuid4(), s3_key="x",
        content_type=ContentType.IMAGE_PNG, filename="x.png", size_bytes=1,
    )
    job = AnalysisJob(
        job_id=uuid4(), session_id=uuid4(), user_id=uuid4(),
        assets=(asset,), prompt_version="v1", submitted_at=datetime.now(UTC),
    )
    report = adapter.analyze(job, {asset.asset_id: b"x"})

    # No retrieved chunks → every risk's citation is "phantom" → all dropped.
    assert report.risks == ()
    # Other report fields should still be populated from the emit fixture.
    assert len(report.components) == 3
