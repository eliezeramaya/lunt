from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Quote
from api.schemas.confirm import ConfirmRequest, ConfirmResponse
from api.services.db import get_db

router = APIRouter(prefix="/v1", tags=["confirm"])


@router.post("/confirm", response_model=ConfirmResponse)
async def confirm_quote(
    request: ConfirmRequest,
    db: AsyncSession = Depends(get_db),
) -> ConfirmResponse:
    """
    Confirma y guarda una cotización calculada

    Crea un registro inmutable en la base de datos con:
    - **Número de cotización único**
    - **Snapshot completo del cálculo**
    - **Metadata y notas**

    La cotización queda guardada para trazabilidad histórica.
    """
    try:
        data = request.calculated_data

        year = datetime.now().year
        from sqlalchemy import func, select

        count_query = select(func.count(Quote.id)).where(
            func.extract("year", Quote.created_at) == year
        )
        result = await db.execute(count_query)
        count = result.scalar() or 0

        quote_number = f"QUOT-{year}-{count + 1:04d}"

        quote = Quote(
            user_id=request.user_id,
            quote_number=quote_number,
            concept_code=data["concept_code"],
            concept_description=data["concept_description"],
            location_code=data["location_code"],
            calculation_date=datetime.fromisoformat(data["calculation_date"]),
            breakdown=data["breakdown"],
            costo_directo=Decimal(str(data["costo_directo"])),
            indirectos=Decimal(str(data["indirectos"])),
            utilidad=Decimal(str(data["utilidad"])),
            precio_unitario=Decimal(str(data["precio_unitario"])),
            indirect_percentage=Decimal(str(data["indirect_percentage"])),
            utility_percentage=Decimal(str(data["utility_percentage"])),
            notes=request.notes,
            status="confirmed",
        )

        db.add(quote)
        await db.commit()
        await db.refresh(quote)

        return ConfirmResponse(
            quote_number=quote.quote_number,
            message="Cotizacion confirmada exitosamente",
            quote_id=quote.id,
        )

    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Campo faltante en calculated_data: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al confirmar cotizacion: {str(e)}")
