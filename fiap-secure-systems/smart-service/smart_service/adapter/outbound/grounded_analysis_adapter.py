"""GroundedAnalysisAdapter — composes extract → canonicalize → retrieve → emit.

Implements AnalysisModelPort so it is a drop-in replacement for ClaudeModelAdapter
when SMART_ANALYSIS_STRATEGY=grounded. Risks without at least one citation
referencing a retrieved chunk are dropped before the StructuredReport is
returned (hallucination filter).
"""
from __future__ import annotations

import time
from typing import Any
from uuid import UUID

import anthropic
import structlog

from smart_service.domain.citation import Citation
from smart_service.infrastructure.metrics import record_anthropic_call_duration_ms  # noqa: I001
from smart_service.domain.corpus import PatternMatch
from smart_service.domain.graph import CanonicalKind, ComponentGraph
from smart_service.domain.model import (
    AnalysisJob,
    Component,
    ComponentKind,
    Confidence,
    ImpactEffort,
    Improvement,
    ModelMetadata,
    Relevance,
    Risk,
    RiskCategory,
    Severity,
    Strength,
    StructuredReport,
)
from smart_service.domain.ports import (
    AnalysisModelError,
    CanonicalizerPort,
    ComponentExtractorPort,
    EmbeddingPort,
    PatternRetrievalPort,
)

log = structlog.get_logger(__name__)

_SYSTEM = """You are an expert system-architecture reviewer.

You will be given:
  1. A canonical component graph extracted from a diagram.
  2. A bank of retrieved pattern excerpts (from a curated corpus) that may apply.

Produce an architecture review by calling submit_analysis_report. Every risk
you raise MUST cite at least one of the provided corpus chunks (by doc_id +
chunk_index). If a concern is not supported by a retrieved chunk, do not raise
it as a risk — put it in improvements instead. Use evidence from the graph.

Output ONLY the tool call.
"""


def _emit_tool() -> dict[str, Any]:
    return {
        "name": "submit_analysis_report",
        "description": "Submit a grounded architecture review.",
        "input_schema": {
            "type": "object",
            "required": ["summary", "confidence", "components", "risks",
                         "improvements", "strengths"],
            "properties": {
                "summary": {"type": "string"},
                "confidence": {"type": "string",
                               "enum": [c.value for c in Confidence]},
                "components": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["name", "kind", "responsibility",
                                     "relevance", "evidence"],
                        "properties": {
                            "name": {"type": "string"},
                            "kind": {"type": "string",
                                     "enum": [k.value for k in ComponentKind]},
                            "responsibility": {"type": "string"},
                            "relevance": {"type": "string",
                                          "enum": [r.value for r in Relevance]},
                            "evidence": {"type": "string"},
                        },
                    },
                },
                "risks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["title", "category", "severity",
                                     "description", "affected_components",
                                     "recommendation"],
                        "properties": {
                            "title": {"type": "string"},
                            "category": {"type": "string",
                                         "enum": [c.value for c in RiskCategory]},
                            "severity": {"type": "string",
                                         "enum": [s.value for s in Severity]},
                            "description": {"type": "string"},
                            "affected_components": {"type": "array",
                                                    "items": {"type": "string"}},
                            "recommendation": {"type": "string"},
                            "citations": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["doc_id", "chunk_index"],
                                    "properties": {
                                        "doc_id": {"type": "string"},
                                        "chunk_index": {"type": "integer"},
                                    },
                                },
                            },
                        },
                    },
                },
                "improvements": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["title", "rationale", "impact", "effort",
                                     "affected_components"],
                        "properties": {
                            "title": {"type": "string"},
                            "rationale": {"type": "string"},
                            "impact": {"type": "string",
                                       "enum": [i.value for i in ImpactEffort]},
                            "effort": {"type": "string",
                                       "enum": [i.value for i in ImpactEffort]},
                            "affected_components": {"type": "array",
                                                    "items": {"type": "string"}},
                        },
                    },
                },
                "strengths": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["title", "description"],
                        "properties": {
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                        },
                    },
                },
            },
        },
    }


class GroundedAnalysisAdapter:
    def __init__(
        self,
        *,
        extractor: ComponentExtractorPort,
        canonicalizer: CanonicalizerPort,
        embedder: EmbeddingPort,
        retriever: PatternRetrievalPort,
        anthropic_client: Any,  # anthropic.Anthropic — typed as Any so tests can sub
        model: str,
        top_k_per_component: int = 3,
        top_k_topology: int = 5,
    ) -> None:
        self._extractor = extractor
        self._canonicalizer = canonicalizer
        self._embedder = embedder
        self._retriever = retriever
        self._client = anthropic_client
        self._model = model
        self._k_comp = top_k_per_component
        self._k_topology = top_k_topology

    def analyze(
        self,
        job: AnalysisJob,
        asset_bytes: dict[UUID, bytes],
    ) -> StructuredReport:
        started = time.monotonic()

        # Stage 1+2: extract + canonicalise
        assets = [
            (a.content_type.value, asset_bytes[a.asset_id]) for a in job.assets
        ]
        graph = self._extractor.extract(assets)
        graph = self._canonicalizer.canonicalize(graph)

        # Stage 3: retrieve per-component, per-edge-protocol, and topology
        retrieved = self._retrieve(graph)

        # Stage 7: schema-bound emission with the retrieved bank in-prompt
        payload, tokens_in, tokens_out, model_name = self._emit(job, graph, retrieved)
        elapsed_ms = int((time.monotonic() - started) * 1000)

        return self._payload_to_report(
            payload, retrieved,
            tokens_in=tokens_in, tokens_out=tokens_out,
            duration_ms=elapsed_ms, model=model_name,
        )

    def _retrieve(self, graph: ComponentGraph) -> dict[str, PatternMatch]:
        seen: dict[str, PatternMatch] = {}

        comp_queries = [
            f"{c.kind.value}: {c.label}"
            for c in graph.components
            if c.kind is not CanonicalKind.UNKNOWN
        ]
        comp_tags = [
            [c.kind.value] for c in graph.components
            if c.kind is not CanonicalKind.UNKNOWN
        ]

        edge_queries = [
            f"{e.protocol.value} from {e.from_node} to {e.to_node}"
            for e in graph.edges
        ]
        edge_tags = [[e.protocol.value] for e in graph.edges]

        topology = self._describe_topology(graph)

        if not (comp_queries or edge_queries):
            self._merge(seen, self._search([topology], [[]], self._k_topology))
            return seen

        self._merge(seen, self._search(comp_queries, comp_tags, self._k_comp))
        self._merge(seen, self._search(edge_queries, edge_tags, self._k_comp))
        self._merge(seen, self._search([topology], [[]], self._k_topology))
        return seen

    def _search(
        self,
        queries: list[str],
        tag_lists: list[list[str]],
        top_k: int,
    ) -> list[PatternMatch]:
        if not queries:
            return []
        vecs = self._embedder.embed_query(queries)
        out: list[PatternMatch] = []
        for vec, tags in zip(vecs, tag_lists, strict=True):
            out.extend(self._retriever.search(vec, tags, top_k))
        return out

    @staticmethod
    def _merge(into: dict[str, PatternMatch], items: list[PatternMatch]) -> None:
        for m in items:
            key = f"{m.doc_id}#{m.chunk_index}"
            if key not in into or m.score > into[key].score:
                into[key] = m

    @staticmethod
    def _describe_topology(graph: ComponentGraph) -> str:
        kinds = sorted({c.kind.value for c in graph.components})
        protos = sorted({e.protocol.value for e in graph.edges})
        return (
            f"Architecture with components: {', '.join(kinds)}. "
            f"Interactions over: {', '.join(protos) or 'none'}. "
            f"{len(graph.components)} components, {len(graph.edges)} edges."
        )

    def _emit(
        self,
        job: AnalysisJob,
        graph: ComponentGraph,
        retrieved: dict[str, PatternMatch],
    ) -> tuple[dict[str, Any], int, int, str]:
        retrieved_block = self._format_retrieved(retrieved)
        graph_block = self._format_graph(graph)
        user = (
            f"## Architecture Graph\n{graph_block}\n\n"
            f"## Retrieved patterns (cite by doc_id + chunk_index)\n{retrieved_block}\n\n"
            f"Submit submit_analysis_report now."
        )
        started = time.monotonic()
        status = "ok"
        try:
            resp = self._client.messages.create(
                model=self._model,
                max_tokens=8192,
                system=[{"type": "text", "text": _SYSTEM,
                         "cache_control": {"type": "ephemeral"}}],
                tools=[_emit_tool()],
                tool_choice={"type": "tool", "name": "submit_analysis_report"},
                messages=[{"role": "user", "content": user}],
            )
        except anthropic.APIStatusError as e:
            code = "MODEL_RATE_LIMITED" if e.status_code == 429 else "MODEL_API_ERROR"
            status = "rate_limited" if e.status_code == 429 else "error"
            raise AnalysisModelError(code, str(e)) from e
        except anthropic.APIError as e:
            status = "error"
            raise AnalysisModelError("MODEL_API_ERROR", str(e)) from e
        finally:
            record_anthropic_call_duration_ms(
                (time.monotonic() - started) * 1000, self._model, status
            )

        tool_call = next(
            (b for b in resp.content if getattr(b, "type", None) == "tool_use"),
            None,
        )
        if tool_call is None:
            raise AnalysisModelError(
                "MODEL_OUTPUT_INVALID",
                f"no tool_use block; stop_reason={getattr(resp, 'stop_reason', '?')}",
            )
        return (
            tool_call.input,
            getattr(resp.usage, "input_tokens", 0) or 0,
            getattr(resp.usage, "output_tokens", 0) or 0,
            getattr(resp, "model", self._model) or self._model,
        )

    @staticmethod
    def _format_graph(graph: ComponentGraph) -> str:
        comps = "\n".join(
            f"- {c.node_id} ({c.kind.value}): {c.label}" for c in graph.components
        )
        edges = "\n".join(
            f"- {e.from_node} --[{e.protocol.value}: {e.label}]--> {e.to_node}"
            for e in graph.edges
        )
        return f"Components:\n{comps}\n\nEdges:\n{edges or '(none)'}"

    @staticmethod
    def _format_retrieved(retrieved: dict[str, PatternMatch]) -> str:
        if not retrieved:
            return "(no retrieved patterns)"
        return "\n\n".join(
            f"### {m.doc_id} chunk {m.chunk_index} (score {m.score:.2f}) "
            f"— {m.title} [{m.source}]\n{m.content}"
            for m in sorted(retrieved.values(), key=lambda x: -x.score)
        )

    def _payload_to_report(
        self,
        p: dict[str, Any],
        retrieved: dict[str, PatternMatch],
        *,
        tokens_in: int,
        tokens_out: int,
        duration_ms: int,
        model: str,
    ) -> StructuredReport:
        idx = {f"{m.doc_id}#{m.chunk_index}": m for m in retrieved.values()}

        risks_with_citations: list[Risk] = []
        dropped = 0
        for r in p.get("risks", []):
            cit_list = r.get("citations", []) or []
            citations: list[Citation] = []
            for c in cit_list:
                key = f"{c['doc_id']}#{c['chunk_index']}"
                if key in idx:
                    m = idx[key]
                    citations.append(Citation(
                        doc_id=m.doc_id, source=m.source, title=m.title,
                        chunk_index=m.chunk_index, score=m.score,
                    ))
            if not citations:
                dropped += 1
                log.info("grounded.dropped_uncited_risk", title=r.get("title"))
                continue
            risks_with_citations.append(Risk(
                title=r["title"],
                category=RiskCategory(r["category"]),
                severity=Severity(r["severity"]),
                description=r["description"],
                affected_components=tuple(r.get("affected_components", [])),
                recommendation=r["recommendation"],
                citations=tuple(citations),
            ))
        if dropped:
            log.info("grounded.hallucination_filter", dropped=dropped)

        return StructuredReport(
            summary=p["summary"],
            confidence=Confidence(p["confidence"]),
            components=tuple(
                Component(
                    name=c["name"],
                    kind=ComponentKind(c["kind"]),
                    responsibility=c["responsibility"],
                    relevance=Relevance(c["relevance"]),
                    evidence=c["evidence"],
                )
                for c in p["components"]
            ),
            risks=tuple(risks_with_citations),
            improvements=tuple(
                Improvement(
                    title=i["title"],
                    rationale=i["rationale"],
                    impact=ImpactEffort(i["impact"]),
                    effort=ImpactEffort(i["effort"]),
                    affected_components=tuple(i.get("affected_components", [])),
                )
                for i in p.get("improvements", [])
            ),
            strengths=tuple(
                Strength(title=s["title"], description=s["description"])
                for s in p.get("strengths", [])
            ),
            model_metadata=ModelMetadata(
                model=model, tokens_in=tokens_in, tokens_out=tokens_out,
                duration_ms=duration_ms,
            ),
        )
