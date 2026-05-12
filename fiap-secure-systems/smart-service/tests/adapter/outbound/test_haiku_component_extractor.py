from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from smart_service.adapter.outbound.haiku_component_extractor import (
    HaikuComponentExtractor,
)
from smart_service.domain.graph import CanonicalKind, EdgeProtocol
from smart_service.domain.ports import AnalysisModelError

FIXTURE = Path(__file__).parents[2] / "fixtures" / "grounded" / "extractor_tool_use_response.json"


class _ResponseFromDict:
    def __init__(self, data: dict) -> None:
        self.id = data["id"]
        self.model = data["model"]
        self.stop_reason = data["stop_reason"]
        self.content = [SimpleNamespace(**block) for block in data["content"]]
        self.usage = SimpleNamespace(**data["usage"])


class _FakeClient:
    def __init__(self, response: object) -> None:
        self._response = response
        self.last_call: dict = {}
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kw):
        self.last_call = kw
        if isinstance(self._response, Exception):
            raise self._response
        return self._response


def _fake_response(payload: dict) -> _ResponseFromDict:
    return _ResponseFromDict(payload)


def test_extract_returns_canonical_graph_from_tool_use():
    response = json.loads(FIXTURE.read_text())
    client = _FakeClient(_fake_response(response))
    extractor = HaikuComponentExtractor(client=client, model="claude-haiku-4-5-20251001")

    graph = extractor.extract([("image/png", b"\x89PNG\r\n\x1a\n...")])

    assert len(graph.components) == 4
    assert graph.components[2].kind is CanonicalKind.COMPUTE_CONTAINER
    assert graph.edges[2].protocol is EdgeProtocol.DB_QUERY
    sent = client.last_call
    assert sent["tool_choice"] == {"type": "tool", "name": "submit_component_graph"}
    assert sent["tools"][0]["name"] == "submit_component_graph"
    # The image must be base64-encoded into the user content
    user_content = sent["messages"][0]["content"]
    image_block = next(b for b in user_content if b["type"] == "image")
    assert image_block["source"]["media_type"] == "image/png"
    assert image_block["source"]["type"] == "base64"


def test_extract_raises_when_model_did_not_call_tool():
    response = {
        "id": "x", "model": "m", "stop_reason": "end_turn",
        "usage": {"input_tokens": 1, "output_tokens": 1},
        "content": [{"type": "text", "text": "I'm sorry Dave"}],
    }
    extractor = HaikuComponentExtractor(client=_FakeClient(_fake_response(response)),
                                        model="claude-haiku-4-5-20251001")
    with pytest.raises(AnalysisModelError) as exc:
        extractor.extract([("image/png", b"x")])
    assert exc.value.code == "EXTRACTOR_NO_TOOL_USE"


def test_extract_raises_on_invalid_kind():
    response = {
        "id": "x", "model": "m", "stop_reason": "tool_use",
        "usage": {"input_tokens": 1, "output_tokens": 1},
        "content": [{
            "type": "tool_use", "id": "t", "name": "submit_component_graph",
            "input": {
                "components": [{"node_id": "n1", "label": "x", "kind": "not-a-real-kind"}],
                "edges": [],
            },
        }],
    }
    extractor = HaikuComponentExtractor(client=_FakeClient(_fake_response(response)),
                                        model="claude-haiku-4-5-20251001")
    with pytest.raises(AnalysisModelError) as exc:
        extractor.extract([("image/png", b"x")])
    assert exc.value.code == "EXTRACTOR_INVALID_OUTPUT"


def test_extract_handles_pdf_assets():
    response = json.loads(FIXTURE.read_text())
    client = _FakeClient(_fake_response(response))
    extractor = HaikuComponentExtractor(client=client, model="m")
    extractor.extract([("application/pdf", b"%PDF-1.4...")])
    user_content = client.last_call["messages"][0]["content"]
    doc_block = next(b for b in user_content if b["type"] == "document")
    assert doc_block["source"]["media_type"] == "application/pdf"


def test_extract_maps_api_error_to_analysis_model_error():
    import anthropic

    class _ApiErr(anthropic.APIError):
        def __init__(self):
            self.message = "boom"
        def __str__(self):
            return "boom"

    extractor = HaikuComponentExtractor(
        client=_FakeClient(_ApiErr()), model="m",
    )
    with pytest.raises(AnalysisModelError) as exc:
        extractor.extract([("image/png", b"x")])
    assert exc.value.code == "EXTRACTOR_API_ERROR"


def test_tool_schema_enums_match_canonical_taxonomy():
    """The submit_component_graph tool schema enumerates exactly the canonical kinds + protocols.
    If the taxonomy grows or shrinks, the schema must stay in sync."""
    from smart_service.adapter.outbound.haiku_component_extractor import _TOOL

    schema_props = _TOOL["input_schema"]["properties"]
    component_kinds = schema_props["components"]["items"]["properties"]["kind"]["enum"]
    edge_protocols = schema_props["edges"]["items"]["properties"]["protocol"]["enum"]
    assert set(component_kinds) == {k.value for k in CanonicalKind}
    assert set(edge_protocols) == {p.value for p in EdgeProtocol}
