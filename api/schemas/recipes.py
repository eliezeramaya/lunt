from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class RecipeSelectionMode(str, Enum):
    aggregate = "aggregate"
    single = "single"
    strategy = "strategy"


class RecipeStrategy(str, Enum):
    cheapest = "cheapest"
    strongest = "strongest"  # placeholder
    latest = "latest"


class RecipeRequestParams(BaseModel):
    concepto_codigo: str
    fecha: date
    ubicacion_codigo: str
    selection_mode: RecipeSelectionMode = RecipeSelectionMode.aggregate
    recipe_variant_id: Optional[str] = None
    strategy: Optional[RecipeStrategy] = None
    allow_missing_prices: bool = False
    locale: str = "es-MX"

    @field_validator("concepto_codigo")
    @classmethod
    def _norm_concept(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("ubicacion_codigo")
    @classmethod
    def _norm_loc(cls, v: str) -> str:
        return v.strip().upper()


class RecipePreviewInsumo(BaseModel):
    insumo_codigo: str
    cantidad: Decimal
    unidad: str
    precio_unitario: Decimal | None
    moneda: str | None
    source_variant_id: str
    warnings: list[str] = []


class RecipePreviewVariant(BaseModel):
    variant_id: str
    variant_label: str
    receta_codigo: str | None = None
    aggregated_cost: Decimal | None = None
    warnings: list[str] = []


class RecipePreview(BaseModel):
    concepto_codigo: str
    selection_mode: RecipeSelectionMode
    used_variant_id: str | None = None
    used_strategy: RecipeStrategy | None = None
    variants_considered: list[RecipePreviewVariant]
    insumos: list[RecipePreviewInsumo]
    warnings: list[str] = []
    errors: list[str] = []

