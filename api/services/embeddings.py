from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol


class EmbeddingModel(Protocol):
    dim: int
    name: str

    def embed(self, text: str, lang: str = "es") -> list[float]:  # pragma: no cover - protocol
        ...


@dataclass
class LocalSentenceEncoder:
    """
    Embedding model sin dependencias externas.
    Implementación determinista basada en hashing simple a un vector de tamaño fijo.

    Nota: Este modelo NO es semántico, pero es suficiente para pruebas locales y evita
    dependencia de red. En producción, reemplace por un modelo real (e.g., SentenceTransformers).
    """

    dim: int = 384
    name: str = "torch-mini-emb-384-local"

    def embed(self, text: str, lang: str = "es") -> list[float]:
        import math

        t = " ".join(text.strip().lower().split())
        vec = [0.0] * self.dim
        # simple char-hash folding
        for i, ch in enumerate(t.encode("utf-8")):
            vec[i % self.dim] += (ch % 13) / 13.0
        # L2 normalize
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

