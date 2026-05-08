"""Operational REST adapter — health, readiness, admin replay."""
from __future__ import annotations

import hashlib
import hmac
import time
from typing import Protocol

from fastapi import APIRouter, HTTPException, Request, status

REPLAYABLE_QUEUES = frozenset({"analysis-jobs-dlq", "analysis-results-dlq"})
HMAC_REPLAY_WINDOW_SECONDS = 300


class DlqReplayerPort(Protocol):
    def replay_dlq(self, queue: str) -> int: ...


def build_router(
    *,
    internal_hmac_secret: str,
    replayer: DlqReplayerPort,
) -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @router.get("/readiness")
    def readiness() -> dict[str, str]:
        return {"status": "ready"}

    @router.post("/admin/replay/{queue}", status_code=status.HTTP_202_ACCEPTED)
    async def admin_replay(queue: str, request: Request) -> dict[str, int | str]:
        if queue not in REPLAYABLE_QUEUES:
            raise HTTPException(
                status_code=400, detail=f"replay not supported for queue {queue!r}"
            )
        body = await request.body()
        _verify_hmac(
            request.method, request.url.path, body,
            request.headers, secret=internal_hmac_secret,
        )
        replayed = replayer.replay_dlq(queue)
        return {"queue": queue, "replayed": replayed}

    return router


def _verify_hmac(
    method: str,
    path: str,
    body: bytes,
    headers: object,
    *,
    secret: str,
) -> None:
    sig = headers.get("X-Internal-Signature")  # type: ignore[attr-defined]
    ts = headers.get("X-Internal-Timestamp")  # type: ignore[attr-defined]
    if not sig or not ts:
        raise HTTPException(status_code=401, detail="missing internal signature")
    try:
        ts_int = int(ts)
    except ValueError as e:
        raise HTTPException(status_code=401, detail="bad timestamp") from e
    if abs(time.time() - ts_int) > HMAC_REPLAY_WINDOW_SECONDS:
        raise HTTPException(status_code=401, detail="stale timestamp")
    body_hash = hashlib.sha256(body).hexdigest()
    msg = f"{ts_int}\n{method}\n{path}\n{body_hash}".encode()
    expected = hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        raise HTTPException(status_code=401, detail="bad signature")
