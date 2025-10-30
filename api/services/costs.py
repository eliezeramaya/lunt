from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.costs import CostBreakdown, CostParams
from api.schemas.recipes import RecipeRequestParams
from api.services.logging_config import get_logger
from api.services.recipes import get_recipes_for_concept
from api.services.settings import get_settings, resolve_percent, settings
from api.services.pricing_strategies import (
    PricingContext,
    PricingEngine,
    get_pricing_strategy,
)
from api.services.concept_resolver import get_concept_resolver
from api.schemas.nl import ConceptResolution
from api.models import Concept
from api.services.preview_log import create_from_preview


logger = get_logger(__name__)


def _quantize(value: Decimal, scale: int = 4) -> Decimal:
    q = Decimal(10) ** -scale
    return value.quantize(q, rounding=ROUND_HALF_UP)


def _format_output(value: Decimal, decimals: int) -> Decimal:
    q = Decimal(10) ** -decimals
    return value.quantize(q, rounding=ROUND_HALF_UP)


async def compute_cost(
    params: CostParams, db: AsyncSession, *, correlation_id: str | None = None
) -> dict[str, Any]:
    """
    Calcula el costo total con parámetros de porcentajes configurables.

    1) Resuelve porcentajes con precedencia: params > env > fallback
    2) Usa p1.2 para resolver variantes e insumos (ya integra precios vigentes)
    3) Aplica fórmula de costos con Decimal y redondeo HALF_UP
    4) Devuelve preview JSON con breakdown y porcentajes usados
    """
    # 1) Resolver porcentajes
    try:
        _settings = get_settings()
        indirectos_pct = resolve_percent(
            (Decimal(str(params.porcentaje_indirectos)) if params.porcentaje_indirectos is not None else None),
            _settings.default_porc_indirectos,
        )
        utilidad_pct = resolve_percent(
            (Decimal(str(params.porcentaje_utilidad)) if params.porcentaje_utilidad is not None else None),
            _settings.default_porc_utilidad,
        )
        percent_source = {
            "indirectos": "param" if params.porcentaje_indirectos is not None else "env",
            "utilidad": "param" if params.porcentaje_utilidad is not None else "env",
        }
    except ValueError as e:
        return {
            "warnings": [],
            "errors": [str(e)],
        }

    # 2) Resolver concepto por NL si hace falta
    nl_resolution: ConceptResolution | None = None
    if not params.concepto_codigo:
        if not params.description:
            return {"warnings": [], "errors": ["Debe enviar 'concepto_codigo' o 'description'"], "meta": {"error_code": "MISSING_INPUT"}}
        # Resolver
        resolver = await get_concept_resolver(db)
        nl_resolution = await resolver.resolve(
            params.description, language=params.language, topk=get_settings().nl_topk, correlation_id=correlation_id
        )
        threshold = get_settings().nl_score_threshold
        if not nl_resolution.ok or not nl_resolution.concept_code:
            return {
                "warnings": [],
                "errors": ["No se pudo resolver la descripción a un concepto."],
                "meta": {"resolution": nl_resolution.model_dump() if nl_resolution else None, "error_code": "RESOLUTION_FAILED"},
            }
        if nl_resolution.score is None or nl_resolution.score < threshold:
            from api.services.metrics import record_nl_low_confidence
            from lunt.logging import log_event

            record_nl_low_confidence(nl_resolution.backend)
            log_event(
                get_logger(__name__),
                "nl.resolve.warn_low_score",
                "WARNING",
                correlation_id=correlation_id,
                best_code=nl_resolution.concept_code,
                score=nl_resolution.score,
                threshold=threshold,
            )
            return {
                "warnings": ["Confianza insuficiente para determinar el concepto"],
                "errors": [
                    "La descripción no alcanzó el umbral de confianza. Por favor, especifique con más detalle o elija un candidato."
                ],
                "meta": {"resolution": nl_resolution.model_dump(), "error_code": "LOW_CONFIDENCE"},
            }
        params.concepto_codigo = nl_resolution.concept_code

    # Verificar existencia en catálogo; si no existe, devolver 404-like error
    concept_exists = await db.execute(select(Concept).where(Concept.code == params.concepto_codigo))
    if concept_exists.scalar_one_or_none() is None:
        msg = f"El concepto resuelto '{params.concepto_codigo}' no existe en el catálogo"
        log_event(_logger, LogEvt.ERROR, "ERROR", correlation_id=correlation_id, code="CONCEPTO_NO_ENCONTRADO", message=msg)
        return {
            "warnings": [],
            "errors": [msg],
            "meta": {
                "error_code": "RESOLVED_CONCEPT_NOT_FOUND",
                "resolution": (nl_resolution.model_dump() if nl_resolution else {"backend": "bypass", "concept_code": params.concepto_codigo}),
            },
        }

    recipe_req = RecipeRequestParams(
        concepto_codigo=params.concepto_codigo,
        fecha=params.fecha,
        ubicacion_codigo=params.ubicacion_codigo,
        selection_mode=params.selection_mode,
        recipe_variant_id=params.recipe_variant_id,
        strategy=params.strategy,
        allow_missing_prices=params.allow_missing_prices,
    )
    # Logging start event
    from lunt.logging import LogEvt, log_event, timed_section
    from api.services.logging_config import get_logger as _get_logger

    _logger = _get_logger(__name__)

    log_event(
        _logger,
        LogEvt.START,
        "INFO",
        correlation_id=correlation_id,
        concepto_codigo=params.concepto_codigo,
        ubicacion_codigo=params.ubicacion_codigo,
        fecha=params.fecha.isoformat(),
        selection_mode=str(params.selection_mode.value),
        recipe_variant_id=params.recipe_variant_id,
        strategy=(params.strategy.value if params.strategy else None),
        porcentaje_indirectos=float(indirectos_pct),
        porcentaje_utilidad=float(utilidad_pct),
    )

    with timed_section("select") as sel_t:
        recipes_preview = await get_recipes_for_concept(recipe_req, db)
    if recipes_preview.errors and not params.allow_missing_prices:
        # Propagar errores en estricto
        # Log error events
        for err in recipes_preview.errors:
            log_event(
                _logger,
                LogEvt.ERROR,
                "ERROR",
                correlation_id=correlation_id,
                code="VALIDATION_ERROR",
                message=err,
                context={
                    "concepto_codigo": params.concepto_codigo,
                    "ubicacion_codigo": params.ubicacion_codigo,
                    "fecha": params.fecha.isoformat(),
                },
            )
        return {
            "porcentajes_usados": {"indirectos": float(indirectos_pct), "utilidad": float(utilidad_pct)},
            "warnings": recipes_preview.warnings,
            "errors": recipes_preview.errors,
        }

    # 3) Construir contexto y delegar a estrategia
    insumos_ctx = [
        {
            "insumo_codigo": i.insumo_codigo,
            "cantidad": Decimal(str(i.cantidad)),
            "unidad": i.unidad,
            "precio_unitario": (Decimal(str(i.precio_unitario)) if i.precio_unitario is not None else None),
            "moneda": i.moneda,
            "warnings": list(i.warnings),
        }
        for i in recipes_preview.insumos
    ]
    # Build resolution metadata for response/meta
    resolution_meta: dict[str, Any] | None
    if nl_resolution is not None:
        alt_cap = get_settings().nl_topk_alt
        # Prefer explicit alternatives if provided; else derive from candidates
        if nl_resolution.alternatives:
            alt_list = nl_resolution.alternatives[: alt_cap]
            alts = [
                {"concept_code": a.concept_code, "score": round(float(a.score), 2)} for a in alt_list
            ]
        else:
            cands = [(c, s) for c, s in nl_resolution.candidates if c and c != nl_resolution.concept_code]
            alts = [
                {"concept_code": c, "score": round(float(s), 2)} for c, s in cands[: alt_cap]
            ]
        confidence_score = round(float(nl_resolution.score or 0.0), 2)
        # Log confidence and record metrics
        from api.services.metrics import record_nl_confidence
        from lunt.logging import log_event

        record_nl_confidence(nl_resolution.backend, confidence_score, len(alts))
        log_event(
            _logger,
            "nl.resolve.confidence",
            "INFO",
            correlation_id=correlation_id,
            concept_code=params.concepto_codigo,
            confidence_score=confidence_score,
            alternatives=[a["concept_code"] for a in alts],
            backend=nl_resolution.backend,
        )
        resolution_meta = {
            "backend": nl_resolution.backend,
            "concept_code": params.concepto_codigo,
            "confidence_score": confidence_score,
            "alternatives": alts,
            "guidance": nl_resolution.guidance,
        }
    else:
        resolution_meta = {
            "backend": "bypass",
            "concept_code": params.concepto_codigo,
            "confidence_score": 1.0,
            "alternatives": [],
            "guidance": None,
        }

    ctx = PricingContext(
        fecha=params.fecha,
        ubicacion_codigo=params.ubicacion_codigo,
        insumos=insumos_ctx,
        porcentaje_indirectos=Decimal(str(indirectos_pct)),
        porcentaje_utilidad=Decimal(str(utilidad_pct)),
        output_scale_decimals=params.output_scale_decimals,
        allow_missing_prices=params.allow_missing_prices,
        meta={
            "warnings": list(recipes_preview.warnings),
            "variants_considered": [v.model_dump() for v in recipes_preview.variants_considered],
            "used_variant_id": recipes_preview.used_variant_id,
            "used_strategy": recipes_preview.used_strategy,
            "selection_mode": params.selection_mode.value,
            "correlation_id": correlation_id,
            "percent_source": percent_source,
            "resolution": resolution_meta,
        },
    )

    # Log variants considered
    log_event(
        _logger,
        LogEvt.VARIANTS,
        "INFO",
        correlation_id=correlation_id,
        concepto_codigo=params.concepto_codigo,
        variants_considered=[
            {
                "variant_id": v.variant_id,
                "label": v.variant_label,
                "receta_codigo": v.receta_codigo,
                "estimated_cost": (float(v.aggregated_cost) if v.aggregated_cost is not None else None),
            }
            for v in recipes_preview.variants_considered
        ],
        used_variant_id=recipes_preview.used_variant_id,
        used_strategy=(recipes_preview.used_strategy.value if recipes_preview.used_strategy else None),
        notes="; ".join(recipes_preview.warnings) if recipes_preview.warnings else None,
    )

    # Log unit prices batch
    log_event(
        _logger,
        LogEvt.PRICES,
        "DEBUG",
        correlation_id=correlation_id,
        variant_scope=(recipes_preview.used_variant_id or ("multiple" if params.selection_mode.name == "aggregate" else None)),
        items=[
            {
                "insumo_codigo": i.insumo_codigo,
                "cantidad": float(i.cantidad),
                "unidad": i.unidad,
                "precio_unitario": (float(i.precio_unitario) if i.precio_unitario is not None else None),
                "moneda": i.moneda,
                "warnings": i.warnings,
            }
            for i in recipes_preview.insumos
        ],
    )

    strategy = get_pricing_strategy(params.pricing_strategy)
    engine = PricingEngine(strategy)
    with timed_section("compute") as comp_t:
        result = engine.compute(ctx)

    bd = result.breakdown
    # Log final breakdown
    log_event(
        _logger,
        LogEvt.BREAKDOWN_FINAL,
        "INFO",
        correlation_id=correlation_id,
        breakdown={
            "costo_directo": float(bd.costo_directo),
            "indirectos_pct": float(bd.indirectos_pct),
            "indirectos_monto": float(bd.indirectos_monto),
            "subtotal_cd_i": float(bd.subtotal_cd_i),
            "utilidad_pct": float(bd.utilidad_pct),
            "utilidad_monto": float(bd.utilidad_monto),
            "costo_total": float(bd.costo_total),
        },
        warnings_count=len(bd.warnings),
        errors_count=len(bd.errors),
        elapsed_ms=comp_t.get("elapsed_ms", 0.0),
    )

    # End event with timers
    total_ms = 0.0
    validate_ms = 0.0  # Validación se ejecuta dentro de selección en p1.2
    select_ms = comp_t.get("elapsed_ms", 0.0)  # replaced after computing; capture previous
    select_ms = sel_t.get("elapsed_ms", 0.0)
    compute_ms = comp_t.get("elapsed_ms", 0.0)
    total_ms = validate_ms + select_ms + compute_ms
    log_event(
        _logger,
        LogEvt.END,
        "INFO",
        correlation_id=correlation_id,
        elapsed_ms_total=total_ms,
        sections={"validate_ms": validate_ms, "select_ms": select_ms, "compute_ms": compute_ms},
    )

    # 4.2 Preview log (for NL-only invocations)
    if params.description:
        try:
            await create_from_preview(
                db,
                correlation_id=correlation_id,
                description=params.description,
                language=params.language,
                resolution=resolution_meta,
                params={
                    "selection_mode": params.selection_mode.value,
                    "recipe_variant_id": params.recipe_variant_id,
                    "strategy": (params.strategy.value if params.strategy else None),
                    "ubicacion_codigo": params.ubicacion_codigo,
                    "fecha": params.fecha,
                    "porcentaje_indirectos": float(indirectos_pct),
                    "porcentaje_utilidad": float(utilidad_pct),
                },
                preview={
                    "breakdown": {
                        "costo_total": float(bd.costo_total),
                    },
                    "insumos": [i.model_dump() for i in recipes_preview.insumos],
                },
            )
        except Exception:
            pass

    return {
        "concepto_codigo": params.concepto_codigo,
        "selection_mode": params.selection_mode,
        "used_variant_id": recipes_preview.used_variant_id,
        "used_strategy": recipes_preview.used_strategy,
        "variants_considered": [v.model_dump() for v in recipes_preview.variants_considered],
        "insumos": [i.model_dump() for i in recipes_preview.insumos],
        "breakdown": {
            "costo_directo": float(bd.costo_directo),
            "indirectos_pct": float(bd.indirectos_pct),
            "indirectos_monto": float(bd.indirectos_monto),
            "subtotal_cd_i": float(bd.subtotal_cd_i),
            "utilidad_pct": float(bd.utilidad_pct),
            "utilidad_monto": float(bd.utilidad_monto),
            "costo_total": float(bd.costo_total),
        },
        "porcentajes_usados": {
            "indirectos": float(indirectos_pct),
            "utilidad": float(utilidad_pct),
        },
        "meta": result.meta,
        "warnings": bd.warnings,
        "errors": [] if params.allow_missing_prices else recipes_preview.errors or bd.errors,
    }
