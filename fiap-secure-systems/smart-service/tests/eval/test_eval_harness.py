"""Eval suite. Runs the actual grounded pipeline against golden architectures.

Marked `eval` - skipped in default CI. Run with: pytest -m eval

Requires:
- ANTHROPIC_API_KEY in env
- VOYAGE_API_KEY in env
- Docker daemon (Testcontainers pgvector)
- The seed corpus must be ingested (the test ingests it on setup)
"""
from __future__ import annotations

import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
import yaml
from sqlalchemy import create_engine, text
from testcontainers.postgres import PostgresContainer

from smart_service.adapter.outbound.grounded_analysis_adapter import (
    GroundedAnalysisAdapter,
)
from smart_service.adapter.outbound.haiku_canonicalizer import HaikuCanonicalizer
from smart_service.adapter.outbound.haiku_component_extractor import (
    HaikuComponentExtractor,
)
from smart_service.adapter.outbound.pgvector_pattern_retriever import (
    PgVectorPatternRetriever,
)
from smart_service.adapter.outbound.voyage_embedding_adapter import (
    VoyageEmbeddingAdapter,
)
from smart_service.cli.ingest_corpus import ingest
from smart_service.domain.model import AnalysisJob, Asset, ContentType
from tests.eval.scorer import EvalScore, EvalSpec, score

pytestmark = pytest.mark.eval

GOLDEN_DIR = Path(__file__).parent / "golden"


def _golden_ids() -> list[str]:
    return sorted(
        p.name for p in GOLDEN_DIR.iterdir()
        if p.is_dir() and (p / "expected.yaml").is_file()
    )


@pytest.fixture(scope="module")
def adapter():
    """Build the grounded adapter against a fresh Testcontainer Postgres + the live APIs."""
    import anthropic

    if not (os.environ.get("ANTHROPIC_API_KEY") and os.environ.get("VOYAGE_API_KEY")):
        pytest.skip("ANTHROPIC_API_KEY or VOYAGE_API_KEY not set")

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

        client = anthropic.Anthropic()
        with httpx.Client(base_url="https://api.voyageai.com") as voyage:
            embedder = VoyageEmbeddingAdapter(
                api_key=os.environ["VOYAGE_API_KEY"],
                model="voyage-3",
                client=voyage,
            )
            # Ingest the seed corpus
            seed_dir = (
                Path(__file__).resolve().parents[2]
                / "smart_service" / "corpus" / "seed"
            )
            ingest(corpus_dir=seed_dir, engine=engine, embedder=embedder)

            adapter = GroundedAnalysisAdapter(
                extractor=HaikuComponentExtractor(
                    client=client, model="claude-haiku-4-5-20251001"
                ),
                canonicalizer=HaikuCanonicalizer(
                    client=client, model="claude-haiku-4-5-20251001"
                ),
                embedder=embedder,
                retriever=PgVectorPatternRetriever(engine=engine, embedding_dim=1024),
                anthropic_client=client,
                model="claude-sonnet-4-6",
            )
            yield adapter

        engine.dispose()


@pytest.mark.parametrize("arch_id", _golden_ids())
def test_grounded_meets_minimum_quality_bar(adapter, arch_id):
    folder = GOLDEN_DIR / arch_id
    spec_data = yaml.safe_load((folder / "expected.yaml").read_text())
    image_path = folder / "architecture.png"
    spec = EvalSpec(
        architecture_id=spec_data["architecture_id"],
        expected_components=spec_data["expected_components"],
        must_find_risks=spec_data["must_find_risks"],
        forbidden_keywords=spec_data.get("forbidden_keywords", []),
    )

    asset = Asset(
        asset_id=uuid4(), s3_key="x",
        content_type=ContentType.IMAGE_PNG, filename=image_path.name,
        size_bytes=image_path.stat().st_size,
    )
    job = AnalysisJob(
        job_id=uuid4(), session_id=uuid4(), user_id=uuid4(),
        assets=(asset,), prompt_version="v1",
        submitted_at=datetime.now(UTC),
    )
    report = adapter.analyze(job, {asset.asset_id: image_path.read_bytes()})

    s: EvalScore = score(spec, report)
    print(f"\n[{arch_id}] {s}")
    # Tight thresholds; tune after first real-diagram run.
    assert s.component_recall >= 0.70, f"component_recall too low: {s}"
    assert s.risk_recall >= 0.80, f"must_find_risks miss: {s}"
    assert s.citation_rate >= 0.90, f"too many uncited risks: {s}"
    assert s.hallucination_count == 0, f"hallucinations: {s}"
