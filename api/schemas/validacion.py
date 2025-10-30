from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ValidacionParametros(BaseModel):
    """
    Parámetros de validación previa al cálculo de costos.

    - fecha: Fecha de cálculo (YYYY-MM-DD)
    - ubicacion_codigo: Código de ubicación (ej. CDMX)
    - receta_codigos: Códigos de recetas/conceptos a validar
    - allow_missing_prices: Si True, no detiene por faltantes; agrega warnings
    - locale: Locale para mensajes (por ahora, es-MX)
    """

    fecha: date = Field(..., description="Fecha de cálculo en formato ISO (YYYY-MM-DD)")
    ubicacion_codigo: str = Field(..., description="Código de ubicación")
    receta_codigos: list[str] = Field(..., description="Códigos de recetas/conceptos a validar")
    allow_missing_prices: bool = Field(False, description="Permitir faltantes de precio con warnings")
    locale: str = Field("es-MX", description="Locale para mensajes")

    @field_validator("ubicacion_codigo")
    @classmethod
    def _norm_location(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("receta_codigos")
    @classmethod
    def _norm_recipe_codes(cls, v: list[str]) -> list[str]:
        return [code.strip().upper() for code in v]


class InsumoValidado(BaseModel):
    """Representa un insumo validado con su precio vigente (o faltante)."""

    insumo_codigo: str
    cantidad: Decimal
    unidad: str
    precio_unitario: Decimal | None
    moneda: str | None
    warnings: list[str] = []


class RecetaValidada(BaseModel):
    """Resultado de validación por receta/concepto."""

    receta_codigo: str
    insumos: list[InsumoValidado]
    warnings: list[str] = []


class ResultadoValidacion(BaseModel):
    """Resultado global de la validación."""

    ok: bool
    recetas: list[RecetaValidada]
    warnings: list[str]
    errors: list[str]


@dataclass
class ValidationIssue:
    """Estructura uniforme para logging interno de validación."""

    code: str
    severity: Literal["ERROR", "WARNING"]
    context: dict
    message: str

