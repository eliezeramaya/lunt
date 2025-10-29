from typing import Any

from pydantic import BaseModel, Field


class ConfirmRequest(BaseModel):
    """Request para confirmar y guardar cotización"""

    calculated_data: dict[str, Any] = Field(..., description="Datos del cálculo a confirmar")
    notes: str | None = Field(None, description="Notas adicionales")
    user_id: int = Field(1, description="ID del usuario (placeholder)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "calculated_data": {
                        "concept_code": "ALB-001",
                        "precio_unitario": 437.50,
                    },
                    "notes": "Cotizacion para proyecto Torre Central",
                    "user_id": 1,
                }
            ]
        }
    }


class ConfirmResponse(BaseModel):
    """Response al confirmar cotización"""

    quote_number: str = Field(..., description="Número de cotización generado")
    message: str = Field(..., description="Mensaje de confirmación")
    quote_id: int = Field(..., description="ID de la cotización creada")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "quote_number": "QUOT-2025-0001",
                    "message": "Cotizacion confirmada exitosamente",
                    "quote_id": 1,
                }
            ]
        }
    }
