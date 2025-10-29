from datetime import date

from pydantic import BaseModel, Field


class PricePoint(BaseModel):
    """Punto de dato en serie temporal"""

    date: str = Field(..., description="Fecha del precio")
    price: float = Field(..., description="Precio en esa fecha")
    location_code: str = Field(..., description="Código de ubicación")


class SeriesRequest(BaseModel):
    """Request para obtener serie temporal de precios"""

    code: str = Field(..., description="Código del insumo o concepto")
    location_code: str | None = Field("MX-CDMX", description="Código de ubicación")
    start_date: date | None = Field(None, description="Fecha inicial")
    end_date: date | None = Field(None, description="Fecha final")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "code": "MAT-001",
                    "location_code": "MX-CDMX",
                    "start_date": "2024-01-01",
                    "end_date": "2025-01-01",
                }
            ]
        }
    }


class SeriesResponse(BaseModel):
    """Response con serie temporal de precios"""

    code: str
    description: str
    unit: str
    location_code: str
    data_points: list[PricePoint]
    count: int = Field(..., description="Número de puntos en la serie")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "code": "MAT-001",
                    "description": "Block hueco 15x20x40 cm",
                    "unit": "pza",
                    "location_code": "MX-CDMX",
                    "data_points": [
                        {"date": "2024-01-01", "price": 8.00, "location_code": "MX-CDMX"},
                        {"date": "2024-06-01", "price": 8.25, "location_code": "MX-CDMX"},
                        {"date": "2025-01-01", "price": 8.50, "location_code": "MX-CDMX"},
                    ],
                    "count": 3,
                }
            ]
        }
    }
