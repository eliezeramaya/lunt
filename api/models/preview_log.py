from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class PreviewLog(Base, TimestampMixin):
    __tablename__ = "preview_log"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    correlation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    description: Mapped[str] = mapped_column(String, nullable=False)
    language: Mapped[str | None] = mapped_column(String(8), nullable=True)
    inferred_concept_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(nullable=True)
    alternatives: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    final_concept_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    was_correct: Mapped[bool | None] = mapped_column(nullable=True)
    selection_mode: Mapped[str | None] = mapped_column(String(20), nullable=True)
    recipe_variant_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    strategy: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ubicacion_codigo: Mapped[str | None] = mapped_column(String(20), nullable=True)
    fecha: Mapped[date | None] = mapped_column(nullable=True)
    porcentajes: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    preview_summary: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    source_backend: Mapped[str | None] = mapped_column(String(20), nullable=True)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)

