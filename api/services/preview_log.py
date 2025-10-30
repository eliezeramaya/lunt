from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from api.models.preview_log import PreviewLog
from api.services.logging_config import get_logger
from lunt.logging import log_event
from api.services.metrics import record_preview_log_created, record_preview_feedback


logger = get_logger(__name__)


def _truncate(s: str | None, max_len: int = 512) -> str:
    if not s:
        return ""
    s = s.strip()
    return s[:max_len]


async def create_from_preview(
    session: AsyncSession,
    *,
    correlation_id: str | None,
    description: str,
    language: str,
    resolution: dict[str, Any] | None,
    params: dict[str, Any],
    preview: dict[str, Any],
) -> str:
    backend = resolution.get("backend") if resolution else "bypass"
    inferred_code = resolution.get("concept_code") if resolution else None
    confidence = resolution.get("confidence_score") if resolution else None
    alternatives = resolution.get("alternatives") if resolution else None
    selection_mode = params.get("selection_mode")
    recipe_variant_id = params.get("recipe_variant_id")
    strategy = params.get("strategy")
    ubicacion = params.get("ubicacion_codigo")
    fecha = params.get("fecha")
    porcentajes = {
        "indirectos": params.get("porcentaje_indirectos"),
        "utilidad": params.get("porcentaje_utilidad"),
    }
    # Simple preview summary (no PII)
    breakdown = preview.get("breakdown") or {}
    insumos = preview.get("insumos") or []
    top_codes = [i.get("insumo_codigo") for i in insumos[:5]]
    summary = {
        "costo_total": breakdown.get("costo_total"),
        "n_insumos": len(insumos),
        "top_insumos": top_codes,
    }

    row = PreviewLog(
        correlation_id=correlation_id,
        description=_truncate(description),
        language=language,
        inferred_concept_code=inferred_code,
        confidence_score=(float(confidence) if confidence is not None else None),
        alternatives=alternatives,
        final_concept_code=None,
        was_correct=None,
        selection_mode=str(selection_mode) if selection_mode is not None else None,
        recipe_variant_id=recipe_variant_id,
        strategy=(str(strategy) if strategy is not None else None),
        ubicacion_codigo=ubicacion,
        fecha=fecha,
        porcentajes=porcentajes,
        preview_summary=summary,
        source_backend=backend,
    )

    session.add(row)
    await session.flush()
    await session.commit()

    log_event(
        logger,
        "analytics.preview_log.created",
        "INFO",
        correlation_id=correlation_id,
        backend=backend,
        inferred_concept_code=inferred_code,
        confidence_score=confidence,
    )
    record_preview_log_created(backend=backend)
    return row.id


async def mark_user_feedback(
    session: AsyncSession,
    *,
    log_id: str,
    final_concept_code: str,
    was_correct: bool | None,
    notes: str | None = None,
) -> None:
    row = await session.get(PreviewLog, log_id)
    if not row:
        raise ValueError("preview_log id no encontrado")
    row.final_concept_code = final_concept_code
    row.was_correct = was_correct
    row.notes = _truncate(notes, 1024) if notes else None
    await session.flush()
    await session.commit()
    log_event(
        logger,
        "analytics.preview_log.feedback",
        "INFO",
        correlation_id=row.correlation_id,
        final_concept_code=final_concept_code,
        was_correct=was_correct,
    )
    record_preview_feedback(changed=bool(row.inferred_concept_code and row.inferred_concept_code != final_concept_code))

