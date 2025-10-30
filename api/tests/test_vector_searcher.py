from __future__ import annotations

import asyncio
import math
import time

import pytest

from api.services.embeddings import LocalSentenceEncoder
from api.services.vector_search import VectorSearcher


class FakeQdrant:
    def __init__(self, responses):
        self._responses = responses

    def search(self, name: str, vector, topk: int):
        return self._responses[:topk]


class NoopCache:
    async def get(self, key: str):
        return None

    async def set(self, key: str, value, expire: int):
        return None


@pytest.mark.asyncio
async def test_vector_searcher_basic_normalization():
    # Prepare fake response with unnormalized cosine scores [-1..1]
    responses = [
        {"concept_code": "A", "score": 0.9, "payload": {}},
        {"concept_code": "B", "score": 0.7, "payload": {}},
        {"concept_code": "C", "score": 0.1, "payload": {}},
    ]
    searcher = VectorSearcher(qdrant=FakeQdrant(responses), embedder=LocalSentenceEncoder(), collection="c")
    cands = await searcher.search("hola mundo", "es", 3)
    assert cands[0][0] == "A"
    assert 0 <= cands[0][1] <= 1


@pytest.mark.asyncio
async def test_vector_searcher_cache_path():
    called = {"n": 0}

    class CountingQdrant(FakeQdrant):
        def search(self, name, vector, topk):
            called["n"] += 1
            return super().search(name, vector, topk)

    responses = [{"concept_code": "A", "score": 0.9, "payload": {}}]
    searcher = VectorSearcher(
        qdrant=CountingQdrant(responses),
        embedder=LocalSentenceEncoder(),
        collection="c",
        cache=NoopCache(),
        cache_ttl_sec=1,
    )
    await searcher.search("hola", "es", 1)
    await searcher.search("hola", "es", 1)
    # No cache hits because NoopCache returns None; both calls executed
    assert called["n"] == 2

