from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.recipes import RecipePreview, RecipeRequestParams
from api.schemas.costs import CostParams
from api.services.metrics import normalize_concept
from api.schemas.validacion import ResultadoValidacion, ValidacionParametros
from api.services.db import get_db
from api.services.logging_config import get_logger
from api.services.recipes import get_recipes_for_concept
from api.services.costs import compute_cost
from api.services.validacion_insumos_precios import validar_insumos_y_precios


router = APIRouter(prefix="/v1/motor", tags=["motor"])
logger = get_logger(__name__)


@router.post("/validar", response_model=ResultadoValidacion)
async def validar_endpoint(
    params: ValidacionParametros, response: Response, db: AsyncSession = Depends(get_db)
) -> ResultadoValidacion:
    """
    Ejecuta la validación de recetas/insumos y precios vigentes.

    - Añade cabecera `X-Correlation-Id` para trazabilidad.
    - Siempre responde 200 con `ResultadoValidacion` (ok=True/False) para contratos estables.
    """
    correlation_id = str(uuid.uuid4())
    response.headers["X-Correlation-Id"] = correlation_id

    result = await validar_insumos_y_precios(params, db)

    logger.info(
        "Validación ejecutada",
        extra={
            "trace_id": correlation_id,
            "ok": result.ok,
            "warnings_count": len(result.warnings),
            "errors_count": len(result.errors),
        },
    )

    return result


@router.post("/recetas/preview", response_model=RecipePreview)
async def recetas_preview(
    params: RecipeRequestParams, response: Response, db: AsyncSession = Depends(get_db)
) -> RecipePreview:
    """Preview de recetas/variantes por concepto con selección aggregate/single/strategy."""
    correlation_id = str(uuid.uuid4())
    response.headers["X-Correlation-Id"] = correlation_id

    result = await get_recipes_for_concept(params, db)

    logger.info(
        "Recetas preview ejecutada",
        extra={
            "trace_id": correlation_id,
            "concepto": params.concepto_codigo,
            "mode": params.selection_mode,
            "strategy": params.strategy.value if params.strategy else None,
            "variants": len(result.variants_considered),
        },
    )

    return result


@router.post("/costos/preview")
async def costos_preview(
    request: Request, params: CostParams, response: Response, db: AsyncSession = Depends(get_db)
):
    """Preview de costos con parámetros de porcentajes de indirectos/utilidad."""
    correlation_id = str(uuid.uuid4())
    response.headers["X-Correlation-Id"] = correlation_id

    # Attach concept label (with whitelist) to request state for metrics
    try:
        request.state.concepto = normalize_concept(params.concepto_codigo)
    except Exception:
        request.state.concepto = "__unknown__"

    result = await compute_cost(params, db, correlation_id=correlation_id)
    logger.info(
        "Costos preview ejecutada",
        extra={
            "trace_id": correlation_id,
            "concepto": params.concepto_codigo,
            "mode": params.selection_mode,
        },
    )
    try:
        if isinstance(result, dict):
            result.setdefault("meta", {})
            result["meta"]["correlation_id"] = correlation_id
            # Update concepto label based on resolved concept in response
            try:
                concept_from_result = result.get("concepto_codigo") or params.concepto_codigo
                request.state.concepto = normalize_concept(concept_from_result)
            except Exception:
                pass
            # Map error codes to HTTP status
            err_code = result.get("meta", {}).get("error_code")
            if err_code == "RESOLVED_CONCEPT_NOT_FOUND":
                response.status_code = 404
            elif err_code == "LOW_CONFIDENCE":
                response.status_code = 422
            elif err_code == "MISSING_INPUT":
                response.status_code = 400
    except Exception:
        pass
    return result
