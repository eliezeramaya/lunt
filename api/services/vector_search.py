from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from api.services.embeddings import EmbeddingModel, LocalSentenceEncoder
from api.services.logging_config import get_logger
from api.services.metrics import (
    record_nl_vector_confidence,
    record_nl_vector_metrics,
    record_nl_vector_topk,
)
from api.services.qdrant_wrapper import QdrantClientWrapper
from api.services.settings import Settings, get_settings
from lunt.logging import log_event


logger = get_logger(__name__)


class CacheLike:
    async def get(self, key: str) -> Any | None:  # pragma: no cover - interface
        ...

    async def set(self, key: str, value: Any, expire: int) -> None:  # pragma: no cover - interface
        ...


@dataclass
class VectorSearcher:
    qdrant: QdrantClientWrapper
    embedder: EmbeddingModel
    collection: str
    normalize_scores: bool = True
    cache: CacheLike | None = None
    cache_ttl_sec: int = 3600

    async def search(self, description: str, lang: str = "es", topk: int = 5, *, correlation_id: str | None = None) -> list[tuple[str, float]]:
        text = " ".join(description.strip().lower().split())
        cache_key = f"vsearch:{self.collection}:{self.embedder.name}:{lang}:{topk}:{text}"

        if self.cache is not None:
            try:
                cached = await self.cache.get(cache_key)
                if cached is not None:
                    return [(c[0], float(c[1])) for c in cached]
            except Exception:
                pass

        log_event(
            logger,
            "nl.vector.start",
            "INFO",
            correlation_id=correlation_id,
            backend="qdrant",
            description_len=len(text),
            topk=topk,
        )
        start = time.perf_counter()
        vector = self.embedder.embed(text, lang)
        rows = self.qdrant.search(self.collection, vector, topk)
        elapsed = time.perf_counter() - start

        # Extract candidates
        candidates: list[tuple[str, float]] = []
        for r in rows:
            code = r.get("concept_code")
            sc = float(r.get("score", 0.0))
            if self.normalize_scores:
                # Cosine similarity might already be in [0,1], but guard if needed
                # If observed range is [-1,1], map to [0,1]
                if sc < 0 or sc > 1:
                    sc = (sc + 1.0) / 2.0
            candidates.append((code, sc))

        # Sort desc by score
        candidates = [(c, s) for c, s in candidates if c]
        candidates.sort(key=lambda x: x[1], reverse=True)

        record_nl_vector_metrics(ok=bool(candidates), elapsed_seconds=elapsed)
        if candidates:
            record_nl_vector_confidence(candidates[0][1])
            record_nl_vector_topk(len(candidates))

        log_event(
            logger,
            "nl.vector.result",
            "INFO",
            correlation_id=correlation_id,
            best_code=(candidates[0][0] if candidates else None),
            best_score=(candidates[0][1] if candidates else None),
            candidates=[c for c, _ in candidates],
            duration_ms=elapsed * 1000.0,
        )

        if self.cache is not None:
            try:
                await self.cache.set(cache_key, candidates, expire=self.cache_ttl_sec)
            except Exception:
                pass

        return candidates


def from_settings(_settings: Settings | None = None) -> VectorSearcher:
    s = _settings or get_settings()
    embedder: EmbeddingModel = LocalSentenceEncoder(dim=int(getattr(s, "nl_embed_dim", 384)))
    qdrant = QdrantClientWrapper(url=s.nl_qdrant_url, api_key=s.nl_qdrant_api_key)
    # Lazy import Redis cache
    cache = None
    if s.nl_enable_cache:
        from api.services.cache import get_cached, set_cached

        class _RedisCache(CacheLike):
            async def get(self, key: str) -> Any | None:
                return await get_cached(key)

            async def set(self, key: str, value: Any, expire: int) -> None:
                await set_cached(key, value, expire)

        cache = _RedisCache()

    return VectorSearcher(
        qdrant=qdrant,
        embedder=embedder,
        collection=s.nl_qdrant_collection,
        normalize_scores=getattr(s, "nl_normalize_scores", True),
        cache=cache,
        cache_ttl_sec=int(getattr(s, "nl_cache_ttl_sec", 3600)),
    )
