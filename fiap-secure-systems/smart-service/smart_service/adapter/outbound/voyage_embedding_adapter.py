"""Voyage AI embedding adapter. Uses voyage-3 by default (1024-dim, cosine)."""
from __future__ import annotations

import httpx
import structlog

from smart_service.domain.ports import EmbeddingError

log = structlog.get_logger(__name__)


class VoyageEmbeddingAdapter:
    """HTTP client for https://api.voyageai.com/v1/embeddings.

    Caller owns the httpx.Client lifecycle. The composition root constructs one
    client and re-uses it for both query- and document-side embedding calls.
    """

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        client: httpx.Client,
    ) -> None:
        self._key = api_key
        self._model = model
        self._client = client

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self._call(texts, input_type="document")

    def embed_query(self, texts: list[str]) -> list[list[float]]:
        return self._call(texts, input_type="query")

    def _call(self, texts: list[str], *, input_type: str) -> list[list[float]]:
        if not texts:
            return []
        try:
            resp = self._client.post(
                "/v1/embeddings",
                headers={
                    "authorization": f"Bearer {self._key}",
                    "content-type": "application/json",
                },
                json={"input": texts, "model": self._model, "input_type": input_type},
                timeout=httpx.Timeout(30.0, connect=10.0),
            )
        except httpx.HTTPError as e:
            raise EmbeddingError("EMBEDDING_API_ERROR", str(e)) from e
        if resp.status_code == 429:
            raise EmbeddingError("EMBEDDING_RATE_LIMITED", resp.text)
        if resp.status_code >= 400:
            raise EmbeddingError(
                "EMBEDDING_API_ERROR", f"{resp.status_code}: {resp.text}"
            )
        data = resp.json().get("data") or []
        return [item["embedding"] for item in sorted(data, key=lambda x: x["index"])]
