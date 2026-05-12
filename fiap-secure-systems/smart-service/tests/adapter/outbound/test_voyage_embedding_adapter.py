from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from smart_service.adapter.outbound.voyage_embedding_adapter import VoyageEmbeddingAdapter
from smart_service.domain.ports import EmbeddingError

FIXTURES = Path(__file__).parents[2] / "fixtures" / "grounded"


def _transport(handler):
    return httpx.MockTransport(handler)


def _client(handler):
    return httpx.Client(
        transport=_transport(handler), base_url="https://api.voyageai.com"
    )


def test_embeds_two_strings_in_order():
    payload = json.loads((FIXTURES / "voyage_response.json").read_text())

    def handler(req: httpx.Request) -> httpx.Response:
        body = json.loads(req.content)
        assert body["input"] == ["alpha", "beta"]
        assert body["model"] == "voyage-3"
        assert body["input_type"] == "document"
        assert req.headers["authorization"] == "Bearer test-key"
        return httpx.Response(200, json=payload)

    adapter = VoyageEmbeddingAdapter(
        api_key="test-key", model="voyage-3", client=_client(handler),
    )
    out = adapter.embed(["alpha", "beta"])
    assert out == [[0.10, 0.20, 0.30, 0.40], [0.05, 0.15, 0.25, 0.35]]


def test_uses_query_input_type_when_flagged():
    payload = json.loads((FIXTURES / "voyage_response.json").read_text())
    captured: dict = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(req.content)
        return httpx.Response(200, json=payload)

    adapter = VoyageEmbeddingAdapter(
        api_key="k", model="voyage-3", client=_client(handler),
    )
    adapter.embed_query(["a", "b"])
    assert captured["body"]["input_type"] == "query"


def test_surfaces_rate_limit_with_distinct_code():
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"error": {"message": "rate limited"}})

    adapter = VoyageEmbeddingAdapter(
        api_key="k", model="voyage-3", client=_client(handler),
    )
    with pytest.raises(EmbeddingError) as exc:
        adapter.embed(["x"])
    assert exc.value.code == "EMBEDDING_RATE_LIMITED"


def test_surfaces_other_api_errors_as_api_error():
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": {"message": "boom"}})

    adapter = VoyageEmbeddingAdapter(
        api_key="k", model="voyage-3", client=_client(handler),
    )
    with pytest.raises(EmbeddingError) as exc:
        adapter.embed(["x"])
    assert exc.value.code == "EMBEDDING_API_ERROR"


def test_surfaces_transport_errors_as_api_error():
    def handler(req: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("network down")

    adapter = VoyageEmbeddingAdapter(
        api_key="k", model="voyage-3", client=_client(handler),
    )
    with pytest.raises(EmbeddingError) as exc:
        adapter.embed(["x"])
    assert exc.value.code == "EMBEDDING_API_ERROR"


def test_handles_empty_input_without_calling_api():
    def handler(req: httpx.Request) -> httpx.Response:  # pragma: no cover
        raise AssertionError("API should not be called for empty batch")

    adapter = VoyageEmbeddingAdapter(
        api_key="k", model="voyage-3", client=_client(handler),
    )
    assert adapter.embed([]) == []


def test_preserves_order_when_api_returns_out_of_order():
    payload = {
        "object": "list",
        "data": [
            {"object": "embedding", "index": 1, "embedding": [0.0, 1.0]},
            {"object": "embedding", "index": 0, "embedding": [1.0, 0.0]},
        ],
        "model": "voyage-3",
        "usage": {"total_tokens": 4},
    }

    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    adapter = VoyageEmbeddingAdapter(
        api_key="k", model="voyage-3", client=_client(handler),
    )
    out = adapter.embed(["first", "second"])
    assert out == [[1.0, 0.0], [0.0, 1.0]]
