from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from smart_service.adapter.outbound.haiku_canonicalizer import HaikuCanonicalizer
from smart_service.domain.graph import (
    CanonicalKind,
    ComponentGraph,
    EdgeProtocol,
    GraphComponent,
    GraphEdge,
)

FIXTURE = (
    Path(__file__).parents[2]
    / "fixtures"
    / "grounded"
    / "canonicalizer_tool_use_response.json"
)


def _response_from(path: Path):
    data = json.loads(path.read_text())
    r = SimpleNamespace()
    r.id = data["id"]
    r.model = data["model"]
    r.stop_reason = data["stop_reason"]
    r.usage = SimpleNamespace(**data["usage"])
    r.content = [SimpleNamespace(**b) for b in data["content"]]
    return r


class _Client:
    def __init__(self, response):
        self._response = response
        self.last_call: dict = {}
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kw):
        self.last_call = kw
        if isinstance(self._response, Exception):
            raise self._response
        return self._response


def _graph_with_unknowns() -> ComponentGraph:
    return ComponentGraph(
        components=(
            GraphComponent(node_id="k1", label="Postgres", kind=CanonicalKind.DB_RELATIONAL),
            GraphComponent(node_id="u1", label="Redis", kind=CanonicalKind.UNKNOWN),
            GraphComponent(node_id="u2", label="Kafka", kind=CanonicalKind.UNKNOWN),
        ),
        edges=(GraphEdge("k1", "u1", EdgeProtocol.DB_QUERY, ""),),
    )


def test_returns_input_unchanged_when_no_unknowns():
    client = _Client(None)
    g = ComponentGraph(
        components=(GraphComponent("n1", "x", CanonicalKind.DB_RELATIONAL),),
        edges=(),
    )
    c = HaikuCanonicalizer(client=client, model="m")
    assert c.canonicalize(g) is g  # identity, not just equality
    assert client.last_call == {}  # API not called


def test_replaces_unknowns_from_tool_response():
    client = _Client(_response_from(FIXTURE))
    c = HaikuCanonicalizer(client=client, model="m")
    out = c.canonicalize(_graph_with_unknowns())
    kinds = {comp.node_id: comp.kind for comp in out.components}
    assert kinds["u1"] is CanonicalKind.DB_KEYVALUE
    assert kinds["u2"] is CanonicalKind.MSG_STREAM
    assert kinds["k1"] is CanonicalKind.DB_RELATIONAL  # unchanged
    # Edges untouched
    assert out.edges == _graph_with_unknowns().edges


def test_only_unknown_components_are_sent_to_api():
    client = _Client(_response_from(FIXTURE))
    c = HaikuCanonicalizer(client=client, model="m")
    c.canonicalize(_graph_with_unknowns())
    body = client.last_call["messages"][0]["content"]
    assert "Redis" in body
    assert "Kafka" in body
    assert "Postgres" not in body


def test_falls_back_to_input_on_api_error():
    client = _Client(RuntimeError("nope"))
    c = HaikuCanonicalizer(client=client, model="m")
    g = _graph_with_unknowns()
    assert c.canonicalize(g) == g


def test_falls_back_when_no_tool_use_block():
    response = SimpleNamespace(
        id="x", model="m", stop_reason="end_turn",
        usage=SimpleNamespace(input_tokens=1, output_tokens=1),
        content=[SimpleNamespace(type="text", text="I refuse")],
    )
    c = HaikuCanonicalizer(client=_Client(response), model="m")
    g = _graph_with_unknowns()
    assert c.canonicalize(g) == g


def test_falls_back_when_mapping_contains_invalid_kind():
    response = SimpleNamespace(
        id="x", model="m", stop_reason="tool_use",
        usage=SimpleNamespace(input_tokens=1, output_tokens=1),
        content=[SimpleNamespace(
            type="tool_use", id="t", name="submit_canonical_kinds",
            input={"mappings": [{"node_id": "u1", "kind": "garbage"}]},
        )],
    )
    c = HaikuCanonicalizer(client=_Client(response), model="m")
    g = _graph_with_unknowns()
    assert c.canonicalize(g) == g


def test_partial_mapping_only_updates_listed_nodes():
    response = SimpleNamespace(
        id="x", model="m", stop_reason="tool_use",
        usage=SimpleNamespace(input_tokens=1, output_tokens=1),
        content=[SimpleNamespace(
            type="tool_use", id="t", name="submit_canonical_kinds",
            input={"mappings": [{"node_id": "u1", "kind": "db:keyvalue"}]},
        )],
    )
    c = HaikuCanonicalizer(client=_Client(response), model="m")
    out = c.canonicalize(_graph_with_unknowns())
    kinds = {comp.node_id: comp.kind for comp in out.components}
    assert kinds["u1"] is CanonicalKind.DB_KEYVALUE
    assert kinds["u2"] is CanonicalKind.UNKNOWN  # not in mapping → unchanged
