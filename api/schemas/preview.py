from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class InsumoBreakdownItem(BaseModel):
    """Item individual en el desglose de precios"""

    insumo_code: str = Field(..., description="Código del insumo")
    insumo_description: str = Field(..., description="Descripción del insumo")
    unit: str = Field(..., description="Unidad de medida")
    quantity: float = Field(..., gt=0, description="Cantidad requerida")
    price: float = Field(..., ge=0, description="Precio unitario")
    subtotal: float = Field(..., ge=0, description="Subtotal (cantidad x precio)")


class PreviewRequest(BaseModel):
    """Request para generar preview de precio unitario"""

    concept_code: str = Field(..., description="Código del concepto a calcular")
    location_code: Optional[str] = Field(
        "MX-CDMX", description="Código de ubicación para precios regionalizados"
    )
    calculation_date: Optional[date] = Field(None, description="Fecha de cálculo (default: hoy)")

    @field_validator("concept_code")
    @classmethod
    def validate_concept_code(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("location_code")
    @classmethod
    def validate_location_code(cls, v: str) -> str:
        return v.strip().upper()

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "concept_code": "ALB-001",
                    "location_code": "MX-CDMX",
                    "calculation_date": "2025-01-15",
                }
            ]
        }
    }


class PreviewResponse(BaseModel):
    """Response con preview del precio unitario calculado"""

    concept_code: str
    concept_description: str
    concept_unit: str
    location_code: str
    calculation_date: str
    breakdown: List[InsumoBreakdownItem]
    costo_directo: float = Field(..., description="Costo directo de insumos")
    indirectos: float = Field(..., description="Costos indirectos")
    utilidad: float = Field(..., description="Utilidad")
    precio_unitario: float = Field(..., description="Precio unitario total")
    indirect_percentage: float = Field(..., description="Porcentaje de indirectos aplicado")
    utility_percentage: float = Field(..., description="Porcentaje de utilidad aplicado")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "concept_code": "ALB-001",
                    "concept_description": "Muro de block hueco 15x20x40 cm",
                    "concept_unit": "m2",
                    "location_code": "MX-CDMX",
                    "calculation_date": "2025-01-15",
                    "breakdown": [
                        {
                            "insumo_code": "MAT-001",
                            "insumo_description": "Block hueco 15x20x40 cm",
                            "unit": "pza",
                            "quantity": 12.5,
                            "price": 8.50,
                            "subtotal": 106.25,
                        }
                    ],
                    "costo_directo": 350.00,
                    "indirectos": 52.50,
                    "utilidad": 35.00,
                    "precio_unitario": 437.50,
                    "indirect_percentage": 0.15,
                    "utility_percentage": 0.10,
                }
            ]
        }
    }
