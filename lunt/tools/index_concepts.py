from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Concept
from api.services.db import AsyncSessionLocal, init_db
from api.services.embeddings import LocalSentenceEncoder
from api.services.qdrant_wrapper import QdrantClientWrapper
from api.services.settings import get_settings


@dataclass
class ConceptRecord:
    code: str
    name: str
    aliases: list[str]
    tags: list[str]
    lang: str


def build_payload(c: ConceptRecord) -> dict:
    return {
        "concept_code": c.code,
        "concept_name": c.name,
        "aliases": c.aliases,
        "tags": c.tags,
        "lang": c.lang,
    }


async def fetch_concepts(session: AsyncSession) -> list[ConceptRecord]:
    rows = (await session.execute(select(Concept))).scalars().all()
    out: list[ConceptRecord] = []
    for c in rows:
        out.append(ConceptRecord(code=c.code, name=c.description, aliases=[], tags=[], lang="es"))
    return out


async def main() -> None:
    s = get_settings()
    embedder = LocalSentenceEncoder(dim=int(getattr(s, "nl_embed_dim", 384)))
    qdrant = QdrantClientWrapper(url=s.nl_qdrant_url, api_key=s.nl_qdrant_api_key)

    await init_db()
    async with AsyncSessionLocal() as session:
        concepts = await fetch_concepts(session)

    qdrant.ensure_collection(s.nl_qdrant_collection, embedder.dim, distance="Cosine")

    points = []
    for idx, c in enumerate(concepts, start=1):
        text = " ".join([c.name, *c.aliases, *c.tags]).strip().lower()
        vec = embedder.embed(text, c.lang)
        points.append({"id": idx, "vector": vec, "payload": build_payload(c)})

    if points:
        qdrant.upsert_points(s.nl_qdrant_collection, points)
        print(f"Upserted {len(points)} points to {s.nl_qdrant_collection}")
    else:
        print("No concepts found to index")


if __name__ == "__main__":
    asyncio.run(main())

