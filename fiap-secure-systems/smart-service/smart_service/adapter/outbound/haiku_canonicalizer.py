"""Refinement pass over UNKNOWN components using a small Haiku tool-use call."""
from __future__ import annotations

from typing import Any

import structlog

from smart_service.domain.graph import (
    CanonicalKind,
    ComponentGraph,
    GraphComponent,
)

log = structlog.get_logger(__name__)

_SYSTEM = """You are given component labels that an extractor classified as
'unknown'. Submit the most-likely canonical kind for each. If still unsure,
emit 'unknown'.
"""

_TOOL: dict[str, Any] = {
    "name": "submit_canonical_kinds",
    "description": "Submit refined canonical kinds for the listed components.",
    "input_schema": {
        "type": "object",
        "required": ["mappings"],
        "properties": {
            "mappings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["node_id", "kind"],
                    "properties": {
                        "node_id": {"type": "string"},
                        "kind": {
                            "type": "string",
                            "enum": [k.value for k in CanonicalKind],
                        },
                    },
                },
            }
        },
    },
}


class HaikuCanonicalizer:
    def __init__(self, *, client: Any, model: str) -> None:
        self._client = client
        self._model = model

    def canonicalize(self, graph: ComponentGraph) -> ComponentGraph:
        unknowns = [c for c in graph.components if c.kind is CanonicalKind.UNKNOWN]
        if not unknowns:
            return graph

        labels = "\n".join(f"- {c.node_id}: {c.label}" for c in unknowns)
        try:
            resp = self._client.messages.create(
                model=self._model,
                max_tokens=512,
                system=[{"type": "text", "text": _SYSTEM,
                         "cache_control": {"type": "ephemeral"}}],
                tools=[_TOOL],
                tool_choice={"type": "tool", "name": "submit_canonical_kinds"},
                messages=[{"role": "user", "content": labels}],
            )
        except Exception as e:  # best-effort refinement; never narrow this
            log.warning("canonicalizer.api_error", error=str(e))
            return graph

        tool_call = next(
            (b for b in resp.content if getattr(b, "type", None) == "tool_use"),
            None,
        )
        if tool_call is None:
            log.warning("canonicalizer.no_tool_use")
            return graph

        mapping: dict[str, CanonicalKind] = {}
        try:
            for m in tool_call.input["mappings"]:
                mapping[m["node_id"]] = CanonicalKind(m["kind"])
        except (KeyError, ValueError) as e:
            log.warning("canonicalizer.invalid_output", error=str(e))
            return graph

        refined = tuple(
            GraphComponent(c.node_id, c.label, mapping.get(c.node_id, c.kind))
            for c in graph.components
        )
        return ComponentGraph(components=refined, edges=graph.edges)
