from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.preview import PreviewRequest, PreviewResponse
from api.services.db import get_db
from api.services.pricing_engine import PricingEngine

router = APIRouter(prefix="/v1", tags=["preview"])


@router.post("/preview", response_model=PreviewResponse)
async def generate_preview(
    request: PreviewRequest,
    db: AsyncSession = Depends(get_db),
) -> PreviewResponse:
    """
    Genera previsualización del precio unitario de un concepto

    - **concept_code**: Código del concepto a calcular
    - **location_code**: Ubicación para precios regionalizados (default: MX-CDMX)
    - **calculation_date**: Fecha de cálculo (default: hoy)

    Retorna desglose completo con costos directos, indirectos y utilidad.
    """
    try:
        engine = PricingEngine(db)
        result = await engine.build_base_preview(
            concept_code=request.concept_code,
            location_code=request.location_code or "MX-CDMX",
            calculation_date=request.calculation_date,
        )
        return PreviewResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error al calcular preview: {str(e)}"
        ) from e
