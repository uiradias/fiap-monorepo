from __future__ import annotations

import hashlib
import hmac
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from smart_service.adapter.inbound.rest import build_router

SECRET = "x" * 32


class StubReplayer:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def replay_dlq(self, queue: str) -> int:
        self.calls.append(queue)
        return 7


@pytest.fixture()
def app_and_replayer():
    replayer = StubReplayer()
    app = FastAPI()
    app.include_router(
        build_router(internal_hmac_secret=SECRET, replayer=replayer)
    )
    return app, replayer


def _sign(method: str, path: str, body: bytes, ts: int) -> str:
    body_hash = hashlib.sha256(body).hexdigest()
    msg = f"{ts}\n{method}\n{path}\n{body_hash}".encode()
    return hmac.new(SECRET.encode(), msg, hashlib.sha256).hexdigest()


def test_health_is_public(app_and_replayer):
    app, _ = app_and_replayer
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_replay_requires_hmac(app_and_replayer):
    app, _ = app_and_replayer
    client = TestClient(app)
    r = client.post("/admin/replay/analysis-jobs-dlq", json={})
    assert r.status_code == 401


def test_replay_with_valid_hmac(app_and_replayer):
    app, replayer = app_and_replayer
    client = TestClient(app)
    body = b"{}"
    ts = int(time.time())
    sig = _sign("POST", "/admin/replay/analysis-jobs-dlq", body, ts)
    r = client.post(
        "/admin/replay/analysis-jobs-dlq",
        content=body,
        headers={
            "X-Internal-Signature": sig,
            "X-Internal-Timestamp": str(ts),
            "Content-Type": "application/json",
        },
    )
    assert r.status_code == 202
    assert r.json() == {"queue": "analysis-jobs-dlq", "replayed": 7}
    assert replayer.calls == ["analysis-jobs-dlq"]


def test_replay_rejects_old_timestamp(app_and_replayer):
    app, _ = app_and_replayer
    client = TestClient(app)
    body = b"{}"
    ts = int(time.time()) - 600
    sig = _sign("POST", "/admin/replay/analysis-jobs-dlq", body, ts)
    r = client.post(
        "/admin/replay/analysis-jobs-dlq",
        content=body,
        headers={
            "X-Internal-Signature": sig,
            "X-Internal-Timestamp": str(ts),
            "Content-Type": "application/json",
        },
    )
    assert r.status_code == 401


def test_replay_rejects_unknown_queue(app_and_replayer):
    app, _ = app_and_replayer
    client = TestClient(app)
    body = b"{}"
    ts = int(time.time())
    sig = _sign("POST", "/admin/replay/some-other-queue", body, ts)
    r = client.post(
        "/admin/replay/some-other-queue",
        content=body,
        headers={
            "X-Internal-Signature": sig,
            "X-Internal-Timestamp": str(ts),
        },
    )
    assert r.status_code == 400
