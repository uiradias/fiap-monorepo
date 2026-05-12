"""`smart-ingest-corpus` — bulk-load YAML files into corpus tables."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Protocol

import httpx
import structlog
from sqlalchemy import Engine

from smart_service.adapter.outbound.voyage_embedding_adapter import VoyageEmbeddingAdapter
from smart_service.config.settings import Settings
from smart_service.corpus.loader import load_corpus_yaml
from smart_service.corpus.repository import PostgresCorpusRepository
from smart_service.infrastructure.db import build_engine

log = structlog.get_logger(__name__)


class _Embedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


def ingest(*, corpus_dir: Path, engine: Engine, embedder: _Embedder) -> int:
    repo = PostgresCorpusRepository(engine=engine)
    yaml_files = sorted(corpus_dir.glob("*.yaml"))
    total_chunks = 0
    for f in yaml_files:
        doc = load_corpus_yaml(f)
        texts = [c.content for c in doc.chunks]
        embeddings = embedder.embed(texts)
        n = repo.upsert(doc, embeddings)
        total_chunks += n
        log.info("corpus.ingested", doc_id=doc.doc_id, chunks=n, file=str(f))
    return total_chunks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="smart-ingest-corpus")
    parser.add_argument(
        "--dir", type=Path,
        default=Path(__file__).parent.parent / "corpus" / "seed",
        help="Directory containing corpus YAML files (default: bundled seed)",
    )
    args = parser.parse_args(argv)

    settings = Settings()  # type: ignore[call-arg]  # reads env via pydantic-settings
    if settings.voyage_api_key is None:
        print("VOYAGE_API_KEY not set", file=sys.stderr)
        return 2
    engine = build_engine(settings.smart_database_url)
    with httpx.Client(base_url="https://api.voyageai.com") as client:
        embedder = VoyageEmbeddingAdapter(
            api_key=settings.voyage_api_key.get_secret_value(),
            model=settings.voyage_model,
            client=client,
        )
        n = ingest(corpus_dir=args.dir, engine=engine, embedder=embedder)
    print(f"Ingested {n} chunks")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
