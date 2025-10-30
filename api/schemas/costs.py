from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, condecimal

from api.schemas.recipes import RecipeSelectionMode, RecipeStrategy


Fraction = condecimal(ge=0, le=1, max_digits=6, decimal_places=4)


class CostParams(BaseModel):
    fecha: date
    ubicacion_codigo: str
    concepto_codigo: str | None = None
    description: str | None = None
    language: str = "es"
    selection_mode: RecipeSelectionMode = RecipeSelectionMode.aggregate
    recipe_variant_id: str | None = None
    strategy: RecipeStrategy | None = None
    allow_missing_prices: bool = False
    porcentaje_indirectos: Fraction | None = Field(default=None, description="fracción 0..1")
    porcentaje_utilidad: Fraction | None = Field(default=None, description="fracción 0..1")
    output_scale_decimals: int = 2
    locale: str = "es-MX"
    pricing_strategy: str | None = None


class CostBreakdown(BaseModel):
    costo_directo: Decimal
    indirectos_pct: Fraction
    indirectos_monto: Decimal
    subtotal_cd_i: Decimal
    utilidad_pct: Fraction
    utilidad_monto: Decimal
    costo_total: Decimal
