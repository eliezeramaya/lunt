from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.recalc import RecalcRequest, RecalcResponse
from api.services.db import get_db
from api.services.pricing_engine import PricingEngine

router = APIRouter(prefix="/v1", tags=["recalculate"])


@router.post("/recalc", response_model=RecalcResponse)
async def recalculate_price(
    request: RecalcRequest,
    db: AsyncSession = Depends(get_db),
) -> RecalcResponse:
    """
    Recalcula el precio unitario aplicando ajustes

    Permite modificar:
    - **Cantidades y precios de insumos**
    - **Porcentajes de indirectos y utilidad**

    Retorna el nuevo precio unitario recalculado.
    """
    try:
        engine = PricingEngine(db)

        adjustments = {}
        if request.insumo_adjustments:
            adjustments["insumo_adjustments"] = [
                adj.model_dump() for adj in request.insumo_adjustments
            ]
        if request.indirect_percentage is not None:
            adjustments["indirect_percentage"] = request.indirect_percentage
        if request.utility_percentage is not None:
            adjustments["utility_percentage"] = request.utility_percentage

        result = await engine.recalculate_with_adjustments(
            base_preview=request.base_preview,
            adjustments=adjustments,
        )

        return RecalcResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al recalcular: {str(e)}") from e
