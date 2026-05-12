from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from smart_service.adapter.outbound.grounded_analysis_adapter import (
    GroundedAnalysisAdapter,
)
from smart_service.domain.corpus import PatternMatch
from smart_service.domain.graph import (
    CanonicalKind,
    ComponentGraph,
    EdgeProtocol,
    GraphComponent,
    GraphEdge,
)
from smart_service.domain.model import (
    AnalysisJob,
    Asset,
    ContentType,
)

FIXTURE = Path(__file__).parents[2] / "fixtures" / "grounded" / "emit_tool_use_response.json"


class _FakeExtractor:
    def extract(self, _):
        return ComponentGraph(
            components=(
                GraphComponent("n1", "API Gateway", CanonicalKind.NET_GATEWAY),
                GraphComponent("n2", "Auth Svc", CanonicalKind.COMPUTE_CONTAINER),
                GraphComponent("n3", "Users DB", CanonicalKind.DB_RELATIONAL),
            ),
            edges=(
                GraphEdge("n1", "n2", EdgeProtocol.HTTP_SYNC, ""),
                GraphEdge("n2", "n3", EdgeProtocol.DB_QUERY, ""),
            ),
        )


class _Passthrough:
    def canonicalize(self, g):
        return g


class _FakeEmbedder:
    def __init__(self):
        self.queries: list[str] = []

    def embed_query(self, texts):
        self.queries.extend(texts)
        return [[1.0] * 4 for _ in texts]

    def embed(self, texts):
        return self.embed_query(texts)


class _FakeRetriever:
    def __init__(self, return_match: bool = True):
        self.calls: list[list[str]] = []
        self._return_match = return_match

    def search(self, query_embedding, applies_to_any, top_k):
        self.calls.append(applies_to_any)
        if not self._return_match:
            return []
        return [
            PatternMatch(
                doc_id="WA-REL-04-sync-coupling",
                source="aws-well-architected", title="Sync coupling",
                category="reliability", chunk_index=0,
                content="sync chains amplify failure", score=0.88,
            )
        ]


def _fake_anthropic(response_json: dict):
    class _C:
        def __init__(self):
            self.last_call: dict = {}
            self.messages = SimpleNamespace(create=self._c)

        def _c(self, **kw):
            self.last_call = kw
            r = SimpleNamespace()
            r.id = response_json["id"]
            r.model = response_json["model"]
            r.stop_reason = response_json["stop_reason"]
            r.usage = SimpleNamespace(**response_json["usage"])
            r.content = [SimpleNamespace(**b) for b in response_json["content"]]
            return r

    return _C()


def _job() -> AnalysisJob:
    asset = Asset(
        asset_id=uuid4(), s3_key="k", content_type=ContentType.IMAGE_PNG,
        filename="x.png", size_bytes=10,
    )
    return AnalysisJob(
        job_id=uuid4(), session_id=uuid4(), user_id=uuid4(),
        assets=(asset,), prompt_version="v1",
        submitted_at=datetime.now(UTC),
    )


def _adapter(client, *, retriever=None, embedder=None):
    return GroundedAnalysisAdapter(
        extractor=_FakeExtractor(),
        canonicalizer=_Passthrough(),
        embedder=embedder or _FakeEmbedder(),
        retriever=retriever or _FakeRetriever(),
        anthropic_client=client,
        model="claude-sonnet-4-6",
        top_k_per_component=3,
        top_k_topology=3,
    )


def test_pipeline_produces_grounded_report():
    emit_response = json.loads(FIXTURE.read_text())
    client = _fake_anthropic(emit_response)
    retriever = _FakeRetriever()
    adapter = _adapter(client, retriever=retriever)

    job = _job()
    report = adapter.analyze(job, {job.assets[0].asset_id: b"x"})

    assert report.summary.startswith("Three-service")
    assert len(report.components) == 3
    titles = [r.title for r in report.risks]
    assert any("Synchronous auth" in t for t in titles)
    assert not any("Uninvented" in t for t in titles)  # hallucination filter
    # Retrieval was called multiple times (per-component, per-edge, topology)
    assert len(retriever.calls) >= 2


def test_pipeline_passes_corpus_excerpts_into_emit_prompt():
    emit_response = json.loads(FIXTURE.read_text())
    client = _fake_anthropic(emit_response)
    adapter = _adapter(client)
    job = _job()
    adapter.analyze(job, {job.assets[0].asset_id: b"x"})
    sent_messages = client.last_call["messages"]
    body = json.dumps(sent_messages)
    assert "WA-REL-04-sync-coupling" in body
    assert "sync chains amplify failure" in body


def test_risk_with_citation_to_unknown_chunk_is_dropped():
    """If the model invents a citation that doesn't match any retrieved chunk,
    the risk has no valid citations and must be filtered."""
    emit_response = {
        "id": "x", "model": "m", "stop_reason": "tool_use",
        "usage": {"input_tokens": 1, "output_tokens": 1},
        "content": [{
            "type": "tool_use", "id": "t", "name": "submit_analysis_report",
            "input": {
                "summary": "s", "confidence": "high",
                "components": [], "improvements": [], "strengths": [],
                "risks": [{
                    "title": "Risk citing a phantom chunk",
                    "category": "security", "severity": "high",
                    "description": "d", "affected_components": [],
                    "recommendation": "r",
                    "citations": [{"doc_id": "FAKE-DOC-NOT-RETRIEVED",
                                   "chunk_index": 99}],
                }],
            },
        }],
    }
    client = _fake_anthropic(emit_response)
    adapter = _adapter(client)
    job = _job()
    report = adapter.analyze(job, {job.assets[0].asset_id: b"x"})
    assert len(report.risks) == 0


def test_retrieval_queries_use_per_component_and_per_edge_tags():
    """The retriever should be called once per component (filtered by kind),
    once per edge (filtered by protocol), plus once for topology (empty filter)."""
    emit_response = json.loads(FIXTURE.read_text())
    client = _fake_anthropic(emit_response)
    retriever = _FakeRetriever()
    embedder = _FakeEmbedder()
    adapter = _adapter(client, retriever=retriever, embedder=embedder)
    job = _job()
    adapter.analyze(job, {job.assets[0].asset_id: b"x"})

    # Component tags should appear at least once
    flat = [tag for call in retriever.calls for tag in call]
    assert CanonicalKind.NET_GATEWAY.value in flat
    assert CanonicalKind.DB_RELATIONAL.value in flat
    # Edge protocol tags too
    assert EdgeProtocol.HTTP_SYNC.value in flat
    assert EdgeProtocol.DB_QUERY.value in flat
    # At least one empty filter call (topology)
    assert any(len(call) == 0 for call in retriever.calls)


def test_model_metadata_records_tokens_and_duration():
    emit_response = json.loads(FIXTURE.read_text())
    client = _fake_anthropic(emit_response)
    adapter = _adapter(client)
    job = _job()
    report = adapter.analyze(job, {job.assets[0].asset_id: b"x"})
    assert report.model_metadata.tokens_in == 4500
    assert report.model_metadata.tokens_out == 900
    assert report.model_metadata.duration_ms >= 0
    assert report.model_metadata.model == "claude-sonnet-4-6"


def test_emit_called_with_forced_tool_choice():
    emit_response = json.loads(FIXTURE.read_text())
    client = _fake_anthropic(emit_response)
    adapter = _adapter(client)
    job = _job()
    adapter.analyze(job, {job.assets[0].asset_id: b"x"})
    sent = client.last_call
    assert sent["tool_choice"] == {"type": "tool", "name": "submit_analysis_report"}
    assert sent["tools"][0]["name"] == "submit_analysis_report"


def test_pipeline_with_no_retrieval_results_still_returns_a_report():
    """If retrieval returns nothing, the emit prompt still runs but every risk
    will lack a valid citation and get filtered. Empty risks list is valid."""
    emit_response = json.loads(FIXTURE.read_text())
    client = _fake_anthropic(emit_response)
    retriever = _FakeRetriever(return_match=False)
    adapter = _adapter(client, retriever=retriever)
    job = _job()
    report = adapter.analyze(job, {job.assets[0].asset_id: b"x"})
    assert report.risks == ()
    # Other fields should still be present
    assert report.summary == (
        "Three-service web app with synchronous auth chain and an unsharded RDBMS."
    )
    assert len(report.components) == 3
