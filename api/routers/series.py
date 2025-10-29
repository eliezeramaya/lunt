from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Insumo, InsumoPrice
from api.schemas.series import PricePoint, SeriesRequest, SeriesResponse
from api.services.db import get_db

router = APIRouter(prefix="/v1", tags=["series"])


@router.post("/series/insumo", response_model=SeriesResponse)
async def get_insumo_price_series(
    request: SeriesRequest,
    db: AsyncSession = Depends(get_db),
) -> SeriesResponse:
    """
    Obtiene serie temporal de precios para un insumo

    - **code**: Código del insumo
    - **location_code**: Ubicación (default: MX-CDMX)
    - **start_date**: Fecha inicial (default: hace 1 año)
    - **end_date**: Fecha final (default: hoy)

    Retorna lista de precios históricos ordenados por fecha.
    """
    try:
        insumo_query = select(Insumo).where(Insumo.code == request.code)
        result = await db.execute(insumo_query)
        insumo = result.scalar_one_or_none()

        if not insumo:
            raise HTTPException(status_code=404, detail=f"Insumo no encontrado: {request.code}")

        start_date = request.start_date or (datetime.now() - timedelta(days=365)).date()
        end_date = request.end_date or date.today()

        prices_query = (
            select(InsumoPrice)
            .where(
                and_(
                    InsumoPrice.insumo_id == insumo.id,
                    InsumoPrice.location_code == (request.location_code or "MX-CDMX"),
                    InsumoPrice.valid_from >= start_date,
                    InsumoPrice.valid_from <= end_date,
                )
            )
            .order_by(InsumoPrice.valid_from.asc())
        )

        result = await db.execute(prices_query)
        prices = result.scalars().all()

        data_points = [
            PricePoint(
                date=p.valid_from.isoformat(),
                price=float(p.price),
                location_code=p.location_code,
            )
            for p in prices
        ]

        return SeriesResponse(
            code=insumo.code,
            description=insumo.description,
            unit=insumo.unit,
            location_code=request.location_code or "MX-CDMX",
            data_points=data_points,
            count=len(data_points),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error al obtener serie temporal: {str(e)}"
        ) from e


@router.get("/series/concepto/{concept_code}", response_model=SeriesResponse)
async def get_concept_price_series(
    concept_code: str,
    location_code: str = Query("MX-CDMX"),
    db: AsyncSession = Depends(get_db),
) -> SeriesResponse:
    """
    Obtiene serie temporal de precios unitarios para un concepto

    TODO: Implementar cálculo histórico de precios de conceptos
    Por ahora retorna serie vacía como placeholder
    """
    return SeriesResponse(
        code=concept_code,
        description=f"Concepto {concept_code}",
        unit="m2",
        location_code=location_code,
        data_points=[],
        count=0,
    )
