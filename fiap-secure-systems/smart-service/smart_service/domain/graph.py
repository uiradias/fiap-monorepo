"""Canonical architecture-graph value types used by the grounded pipeline.

CanonicalKind / EdgeProtocol are the closed taxonomy retrieval uses to look up
patterns. Free-text labels stay on the components; the canonical kind is what
indexing keys on.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CanonicalKind(StrEnum):
    # Compute
    COMPUTE_CONTAINER = "compute:container"
    COMPUTE_FUNCTION = "compute:function"
    COMPUTE_VM = "compute:vm"
    # Storage
    STORAGE_OBJECT = "storage:object"
    STORAGE_BLOCK = "storage:block"
    # Datastores
    DB_RELATIONAL = "db:relational"
    DB_DOCUMENT = "db:document"
    DB_KEYVALUE = "db:keyvalue"
    DB_TIMESERIES = "db:timeseries"
    DB_GRAPH = "db:graph"
    DB_SEARCH = "db:search"
    # Messaging
    MSG_QUEUE = "msg:queue"
    MSG_TOPIC = "msg:topic"
    MSG_STREAM = "msg:stream"
    # Networking
    NET_GATEWAY = "net:gateway"
    NET_LOADBALANCER = "net:loadbalancer"
    NET_CDN = "net:cdn"
    NET_PROXY = "net:proxy"
    # External / Identity
    EXT_API = "ext:api"
    EXT_USER = "ext:user"
    EXT_THIRDPARTY = "ext:thirdparty"
    IDENTITY_AUTH = "identity:auth"
    IDENTITY_VAULT = "identity:vault"
    # Cache
    CACHE_INMEM = "cache:inmem"
    # Observability
    OBS_LOGGING = "obs:logging"
    OBS_METRICS = "obs:metrics"
    OBS_TRACING = "obs:tracing"
    # Fallback
    UNKNOWN = "unknown"


class EdgeProtocol(StrEnum):
    HTTP_SYNC = "http:sync"
    HTTP_ASYNC = "http:async"
    GRPC = "grpc"
    MESSAGE_QUEUE = "queue"
    PUBSUB = "pubsub"
    STREAM = "stream"
    DB_QUERY = "db:query"
    FILE_RW = "file:rw"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class GraphComponent:
    node_id: str
    label: str
    kind: CanonicalKind


@dataclass(frozen=True, slots=True)
class GraphEdge:
    from_node: str
    to_node: str
    protocol: EdgeProtocol
    label: str


@dataclass(frozen=True, slots=True)
class ComponentGraph:
    components: tuple[GraphComponent, ...]
    edges: tuple[GraphEdge, ...]

    def __post_init__(self) -> None:
        ids = {c.node_id for c in self.components}
        for e in self.edges:
            if e.from_node not in ids or e.to_node not in ids:
                raise ValueError(
                    f"edge {e.from_node}->{e.to_node} references unknown node"
                )
