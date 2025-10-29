from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class InsumoAdjustment(BaseModel):
    """Ajuste a aplicar sobre un insumo específico"""

    insumo_code: str = Field(..., description="Código del insumo a ajustar")
    quantity: Optional[float] = Field(None, gt=0, description="Nueva cantidad")
    price: Optional[float] = Field(None, ge=0, description="Nuevo precio unitario")


class RecalcRequest(BaseModel):
    """Request para recalcular precio con ajustes"""

    base_preview: Dict[str, Any] = Field(..., description="Preview base a modificar")
    insumo_adjustments: Optional[List[InsumoAdjustment]] = Field(
        None, description="Ajustes a insumos"
    )
    indirect_percentage: Optional[float] = Field(
        None, ge=0, le=1, description="Nuevo porcentaje de indirectos"
    )
    utility_percentage: Optional[float] = Field(
        None, ge=0, le=1, description="Nuevo porcentaje de utilidad"
    )

    @field_validator("indirect_percentage", "utility_percentage")
    @classmethod
    def validate_percentage(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0 <= v <= 1):
            raise ValueError("Porcentaje debe estar entre 0 y 1")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "base_preview": {
                        "concept_code": "ALB-001",
                        "breakdown": [],
                        "costo_directo": 350.00,
                    },
                    "insumo_adjustments": [
                        {"insumo_code": "MAT-001", "quantity": 15.0, "price": 9.00}
                    ],
                    "indirect_percentage": 0.18,
                    "utility_percentage": 0.12,
                }
            ]
        }
    }


class RecalcResponse(BaseModel):
    """Response con precio recalculado"""

    concept_code: str
    concept_description: str
    concept_unit: str
    location_code: str
    calculation_date: str
    breakdown: List[Dict[str, Any]]
    costo_directo: float
    indirectos: float
    utilidad: float
    precio_unitario: float
    indirect_percentage: float
    utility_percentage: float
