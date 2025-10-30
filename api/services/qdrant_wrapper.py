from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class QdrantClientWrapper:
    url: str
    api_key: str | None = None

    def __post_init__(self) -> None:
        try:
            from qdrant_client import QdrantClient  # type: ignore
        except Exception as e:  # pragma: no cover - optional dependency path
            self._client = None
            self._import_error = e
        else:
            self._client = QdrantClient(url=self.url, api_key=self.api_key)
            self._import_error = None

    def _require(self) -> Any:
        if self._client is None:  # pragma: no cover
            raise RuntimeError(f"qdrant_client no disponible: {self._import_error}")
        return self._client

    def ensure_collection(self, name: str, dim: int, distance: str = "Cosine") -> None:
        client = self._require()
        from qdrant_client.models import Distance, VectorParams  # type: ignore

        try:
            client.get_collection(name)
        except Exception:
            client.recreate_collection(
                collection_name=name,
                vectors_config=VectorParams(size=dim, distance=getattr(Distance, distance)),
            )

    def upsert_points(self, name: str, points: list[dict]) -> None:
        client = self._require()
        from qdrant_client.models import PointStruct  # type: ignore

        qpoints = [
            PointStruct(id=p.get("id"), vector=p["vector"], payload=p.get("payload", {})) for p in points
        ]
        client.upsert(collection_name=name, points=qpoints)

    def search(self, name: str, vector: list[float], topk: int) -> list[dict]:
        client = self._require()
        res = client.search(collection_name=name, query_vector=vector, limit=topk, with_payload=True)
        out: list[dict] = []
        for pt in res:
            payload = pt.payload or {}
            out.append(
                {
                    "concept_code": payload.get("concept_code") or payload.get("code"),
                    "score": float(pt.score),
                    "payload": payload,
                }
            )
        return out

