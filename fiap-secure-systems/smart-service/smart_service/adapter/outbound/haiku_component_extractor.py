"""Haiku 4.5 vision adapter: extracts a canonical ComponentGraph via tool use."""
from __future__ import annotations

import base64
from typing import Any

import anthropic

from smart_service.domain.graph import (
    CanonicalKind,
    ComponentGraph,
    EdgeProtocol,
    GraphComponent,
    GraphEdge,
)
from smart_service.domain.ports import AnalysisModelError

_SYSTEM = """You analyse architecture diagrams. Call the submit_component_graph
tool with EXACTLY what is visible. Use canonical kinds from the enum — never
invent new values. Use 'unknown' if you can't classify. Generate stable node_ids
like n1, n2, ... for every distinct element. Treat clouds/groups as boundaries
only — do not emit a node for them. Output ONLY the tool call.
"""

_TOOL: dict[str, Any] = {
    "name": "submit_component_graph",
    "description": "Submit the canonical component graph extracted from the diagram.",
    "input_schema": {
        "type": "object",
        "required": ["components", "edges"],
        "properties": {
            "components": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["node_id", "label", "kind"],
                    "properties": {
                        "node_id": {"type": "string"},
                        "label": {"type": "string"},
                        "kind": {
                            "type": "string",
                            "enum": [k.value for k in CanonicalKind],
                        },
                    },
                },
            },
            "edges": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["from_node", "to_node", "protocol", "label"],
                    "properties": {
                        "from_node": {"type": "string"},
                        "to_node": {"type": "string"},
                        "protocol": {
                            "type": "string",
                            "enum": [p.value for p in EdgeProtocol],
                        },
                        "label": {"type": "string"},
                    },
                },
            },
        },
    },
}


class HaikuComponentExtractor:
    def __init__(self, *, client: anthropic.Anthropic, model: str) -> None:
        self._client = client
        self._model = model

    def extract(self, asset_bytes: list[tuple[str, bytes]]) -> ComponentGraph:
        blocks: list[dict[str, Any]] = [
            {"type": "text", "text": "Extract the canonical component graph."}
        ]
        for media_type, data in asset_bytes:
            b64 = base64.b64encode(data).decode("ascii")
            kind = "document" if media_type == "application/pdf" else "image"
            blocks.append({
                "type": kind,
                "source": {"type": "base64", "media_type": media_type, "data": b64},
            })

        try:
            resp = self._client.messages.create(  # type: ignore[call-overload]
                model=self._model,
                max_tokens=2048,
                system=[{"type": "text", "text": _SYSTEM,
                         "cache_control": {"type": "ephemeral"}}],
                tools=[_TOOL],
                tool_choice={"type": "tool", "name": "submit_component_graph"},
                messages=[{"role": "user", "content": blocks}],
            )
        except anthropic.APIError as e:
            raise AnalysisModelError("EXTRACTOR_API_ERROR", str(e)) from e

        tool_call = next(
            (b for b in resp.content if getattr(b, "type", None) == "tool_use"),
            None,
        )
        if tool_call is None:
            raise AnalysisModelError(
                "EXTRACTOR_NO_TOOL_USE",
                f"stop_reason={getattr(resp, 'stop_reason', '?')}",
            )
        payload = tool_call.input  # already a dict from Anthropic SDK
        try:
            return ComponentGraph(
                components=tuple(
                    GraphComponent(
                        node_id=c["node_id"],
                        label=c["label"],
                        kind=CanonicalKind(c["kind"]),
                    )
                    for c in payload["components"]
                ),
                edges=tuple(
                    GraphEdge(
                        from_node=e["from_node"],
                        to_node=e["to_node"],
                        protocol=EdgeProtocol(e["protocol"]),
                        label=e["label"],
                    )
                    for e in payload["edges"]
                ),
            )
        except (KeyError, ValueError) as e:
            raise AnalysisModelError("EXTRACTOR_INVALID_OUTPUT", str(e)) from e
