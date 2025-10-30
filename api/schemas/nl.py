from __future__ import annotations

from pydantic import BaseModel, Field


class ConceptAlternative(BaseModel):
    concept_code: str
    score: float


class ConceptResolution(BaseModel):
    ok: bool
    concept_code: str | None = None
    score: float | None = None
    candidates: list[tuple[str, float]] = Field(default_factory=list)
    guidance: str | None = None
    backend: str = "bypass"
    alternatives: list[ConceptAlternative] = Field(default_factory=list)
