from __future__ import annotations

import time
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Concept
from api.schemas.nl import ConceptResolution
from api.services.logging_config import get_logger
from api.services.metrics import record_nl_low_confidence, record_nl_metrics
from api.services.settings import Settings, get_settings
from api.services.vector_search import VectorSearcher, from_settings as searcher_from_settings
from api.services.cache import get_cached, set_cached
from lunt.logging import LogEvt, log_event


logger = get_logger(__name__)


class IConceptResolver(Protocol):
    async def resolve(self, description: str, language: str = "es", topk: int = 5, *, correlation_id: str | None = None) -> ConceptResolution:  # pragma: no cover - interface
        ...


class SimpleResolver:
    """
    Resolver simple basado en búsqueda LIKE en la tabla de conceptos.
    Actúa como placeholder para backends Qdrant/GPT.
    """

    backend = "qdrant"

    def __init__(self, session: AsyncSession, settings: Settings | None = None):
        self.session = session
        self.settings = settings or get_settings()

    async def resolve(
        self, description: str, language: str = "es", topk: int = 5, *, correlation_id: str | None = None
    ) -> ConceptResolution:
        start = time.perf_counter()
        log_event(
            logger,
            "nl.resolve.start",
            "INFO",
            correlation_id=correlation_id,
            backend=self.backend,
            topk=topk,
            threshold=self.settings.nl_score_threshold,
        )
        desc = " ".join(description.strip().lower().split())
        # Cache key
        if self.settings.nl_enable_cache:
            key = f"nl:{self.backend}:{desc}:{language}:{topk}"
            cached = await get_cached(key)
            if cached is not None:
                return ConceptResolution(**cached)
        q = select(Concept).where(Concept.description.ilike(f"%{desc}%")).limit(topk)
        res = await self.session.execute(q)
        items = list(res.scalars().all())

        candidates: list[tuple[str, float]] = []
        code: str | None = None
        score: float | None = None
        if items:
            for idx, c in enumerate(items):
                sc = 0.9 - idx * 0.05
                candidates.append((c.code, max(sc, 0.5)))
            code, score = candidates[0]
            ok = True
            guidance = None
            # Build alternatives from remaining candidates
            alt_cap = self.settings.nl_topk_alt
            alts = [
                {"concept_code": c, "score": s}
                for c, s in candidates[1 : 1 + max(0, alt_cap)]
                if c and c != code
            ]
        else:
            ok = False
            guidance = "No se encontraron candidatos por descripción."
            alts = []

        elapsed = time.perf_counter() - start
        log_event(
            logger,
            "nl.resolve.result",
            "INFO",
            correlation_id=correlation_id,
            best_code=code,
            score=score,
            candidates=candidates,
            duration_ms=elapsed * 1000.0,
        )
        record_nl_metrics(self.backend, ok, elapsed, resolved_concept=code)
        result = ConceptResolution(
            ok=ok,
            concept_code=code,
            score=score,
            candidates=candidates,
            guidance=guidance,
            backend=self.backend,
        )
        # Populate alternatives as ConceptAlternative models
        from api.schemas.nl import ConceptAlternative

        result.alternatives = [ConceptAlternative(**a) for a in alts]
        if self.settings.nl_enable_cache:
            await set_cached(key, result.model_dump(), expire=600)
        return result


class QdrantResolver(SimpleResolver):
    backend = "qdrant"

    def __init__(self, session: AsyncSession, settings: Settings | None = None, searcher: VectorSearcher | None = None):
        super().__init__(session, settings)
        self._searcher = searcher or searcher_from_settings(self.settings)

    def _embed(self, text: str) -> list[float]:
        # Try OpenAI embedding if available, else simple hash embedding
        try:
            import openai  # type: ignore

            client = openai.OpenAI()
            model = self.settings.nl_embed_model
            resp = client.embeddings.create(model=model, input=text)
            return list(resp.data[0].embedding)
        except Exception:
            # Simple deterministic hashing to 256-dim vector as fallback
            import math

            dims = 256
            vec = [0.0] * dims
            for i, ch in enumerate(text.encode("utf-8")):
                vec[i % dims] += (ch % 13) / 13.0
            # Normalize
            norm = math.sqrt(sum(v * v for v in vec)) or 1.0
            return [v / norm for v in vec]

    async def resolve(
        self, description: str, language: str = "es", topk: int = 5, *, correlation_id: str | None = None
    ) -> ConceptResolution:
        start = time.perf_counter()
        log_event(
            logger,
            "nl.resolve.start",
            "INFO",
            correlation_id=correlation_id,
            backend=self.backend,
            topk=topk,
            threshold=self.settings.nl_score_threshold,
        )
        # Fallback to SimpleResolver if qdrant client is not available
        if getattr(self._searcher.qdrant, "_client", None) is None:
            return await super().resolve(description, language, topk, correlation_id=correlation_id)

        try:
            cands = await self._searcher.search(description, language, topk, correlation_id=correlation_id)
        except Exception as e:
            elapsed = time.perf_counter() - start
            record_nl_metrics(self.backend, False, elapsed, resolved_concept=None)
            return ConceptResolution(ok=False, backend=self.backend, guidance=f"Error en Qdrant: {e}")

        elapsed = time.perf_counter() - start
        ok = bool(cands)
        code = cands[0][0] if ok else None
        score = float(cands[0][1]) if ok else None
        record_nl_metrics(self.backend, ok, elapsed, resolved_concept=code)
        from api.schemas.nl import ConceptAlternative

        alts = [ConceptAlternative(concept_code=c, score=float(s)) for c, s in cands[1:]]
        return ConceptResolution(
            ok=ok,
            concept_code=code,
            score=score,
            alternatives=alts,
            guidance="Búsqueda semántica en Qdrant",
            backend=self.backend,
        )


class GptResolver(SimpleResolver):
    backend = "gpt"

    async def resolve(
        self, description: str, language: str = "es", topk: int = 5, *, correlation_id: str | None = None
    ) -> ConceptResolution:
        # For now, fallback to LIKE but mark backend
        self.backend = "gpt"
        return await super().resolve(description, language, topk, correlation_id=correlation_id)


async def get_concept_resolver(session: AsyncSession, settings: Settings | None = None) -> IConceptResolver:
    _settings = settings or get_settings()
    backend = (_settings.nl_resolver_backend or "qdrant").lower()
    if backend == "qdrant":
        return QdrantResolver(session, _settings)
    if backend == "gpt":
        return GptResolver(session, _settings)
    # fallback simple
    return SimpleResolver(session, _settings)
