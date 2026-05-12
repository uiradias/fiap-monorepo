from __future__ import annotations

import pytest

from smart_service.domain.graph import (
    CanonicalKind,
    ComponentGraph,
    EdgeProtocol,
    GraphComponent,
    GraphEdge,
)


def test_graph_round_trips_components_and_edges():
    g = ComponentGraph(
        components=(
            GraphComponent(node_id="n1", label="API GW", kind=CanonicalKind.NET_GATEWAY),
            GraphComponent(node_id="n2", label="Auth", kind=CanonicalKind.IDENTITY_AUTH),
        ),
        edges=(
            GraphEdge(from_node="n1", to_node="n2", protocol=EdgeProtocol.HTTP_SYNC, label="login"),
        ),
    )
    assert {c.node_id for c in g.components} == {"n1", "n2"}
    assert g.edges[0].protocol is EdgeProtocol.HTTP_SYNC


def test_rejects_edge_referencing_unknown_node():
    with pytest.raises(ValueError):
        ComponentGraph(
            components=(GraphComponent(node_id="n1", label="x", kind=CanonicalKind.UNKNOWN),),
            edges=(GraphEdge(from_node="n1", to_node="n9",
                             protocol=EdgeProtocol.UNKNOWN, label=""),),
        )


def test_canonical_kind_values_match_corpus_vocabulary():
    """The corpus seed files (Task 6) use these exact string values for applies_to.
    If we ever rename, the corpus loses its retrieval target."""
    assert CanonicalKind.NET_GATEWAY.value == "net:gateway"
    assert CanonicalKind.DB_RELATIONAL.value == "db:relational"
    assert CanonicalKind.MSG_QUEUE.value == "msg:queue"
    assert CanonicalKind.MSG_TOPIC.value == "msg:topic"
    assert CanonicalKind.MSG_STREAM.value == "msg:stream"
    assert CanonicalKind.COMPUTE_CONTAINER.value == "compute:container"
    assert CanonicalKind.IDENTITY_VAULT.value == "identity:vault"
    assert CanonicalKind.OBS_TRACING.value == "obs:tracing"
    assert CanonicalKind.UNKNOWN.value == "unknown"


def test_edge_protocol_values_match_corpus_vocabulary():
    assert EdgeProtocol.HTTP_SYNC.value == "http:sync"
    assert EdgeProtocol.HTTP_ASYNC.value == "http:async"
    assert EdgeProtocol.GRPC.value == "grpc"
    assert EdgeProtocol.MESSAGE_QUEUE.value == "queue"
    assert EdgeProtocol.PUBSUB.value == "pubsub"
    assert EdgeProtocol.STREAM.value == "stream"
    assert EdgeProtocol.DB_QUERY.value == "db:query"
    assert EdgeProtocol.FILE_RW.value == "file:rw"
    assert EdgeProtocol.UNKNOWN.value == "unknown"


def test_empty_graph_is_valid():
    g = ComponentGraph(components=(), edges=())
    assert g.components == ()
    assert g.edges == ()
