from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import column
from sqlalchemy.sql.functions import row_number
from sqlalchemy.sql.window import Window

from api.models.concepts import Concept, ConceptRecipe
from api.models.insumos import Insumo, InsumoPrice
from api.models.users_locations import Location
from api.schemas.validacion import (
    InsumoValidado,
    RecetaValidada,
    ResultadoValidacion,
    ValidacionParametros,
    ValidationIssue,
)
from api.services.logging_config import get_logger


logger = get_logger(__name__)


# Repositorio / Queries optimizadas
async def get_ubicacion_by_codigo(session: AsyncSession, codigo: str) -> Location | None:
    q = select(Location).where(Location.code == codigo)
    res = await session.execute(q)
    return res.scalar_one_or_none()


async def get_recetas_with_insumos(
    session: AsyncSession, receta_codigos: list[str], fecha: date
) -> dict[str, list[dict[str, Any]]]:
    """
    Carga recetas activas por código de concepto a la fecha dada, junto con insumos.

    Retorna mapping: concept_code -> list de items {insumo_id, insumo_code, unidad, cantidad}
    """
    # Join Concept -> ConceptRecipe -> Insumo, filtrando por vigencia de receta
    q = (
        select(
            Concept.code.label("concept_code"),
            Insumo.id.label("insumo_id"),
            Insumo.code.label("insumo_code"),
            Insumo.unit.label("unit"),
            ConceptRecipe.quantity.label("quantity"),
        )
        .join(ConceptRecipe, Concept.id == ConceptRecipe.concept_id)
        .join(Insumo, Insumo.id == ConceptRecipe.insumo_id)
        .where(
            and_(
                Concept.code.in_(receta_codigos),
                ConceptRecipe.valid_from <= fecha,
                or_(ConceptRecipe.valid_until.is_(None), ConceptRecipe.valid_until >= fecha),
            )
        )
    )

    rows = (await session.execute(q)).mappings().all()

    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        out[r["concept_code"]].append(
            {
                "insumo_id": int(r["insumo_id"]),
                "insumo_code": str(r["insumo_code"]),
                "unit": str(r["unit"]),
                "quantity": Decimal(str(r["quantity"])),
            }
        )

    # Asegurar claves para conceptos sin recetas activas
    for code in receta_codigos:
        out.setdefault(code, [])

    return out


async def get_precios_vigentes(
    session: AsyncSession, insumo_ids: list[int], location_code: str, fecha: date
) -> dict[int, tuple[Decimal, str]]:
    """
    Obtiene precio vigente por insumo en una sola consulta usando window function.

    Regla de vigencia: valid_from <= fecha AND (valid_until IS NULL OR valid_until >= fecha)
    Selecciona el más reciente (ROW_NUMBER() over insumo_id ORDER BY valid_from DESC = 1)
    """
    if not insumo_ids:
        return {}

    rn = row_number().over(
        partition_by=InsumoPrice.insumo_id, order_by=InsumoPrice.valid_from.desc()
    )

    base = (
        select(
            InsumoPrice.insumo_id.label("insumo_id"),
            InsumoPrice.price.label("price"),
            InsumoPrice.currency.label("currency"),
            rn.label("rn"),
        )
        .where(
            and_(
                InsumoPrice.insumo_id.in_(insumo_ids),
                InsumoPrice.location_code == location_code,
                InsumoPrice.valid_from <= fecha,
                or_(InsumoPrice.valid_until.is_(None), InsumoPrice.valid_until >= fecha),
            )
        )
        .subquery()
    )

    q = select(base.c.insumo_id, base.c.price, base.c.currency).where(base.c.rn == 1)
    rows = (await session.execute(q)).all()
    return {int(r[0]): (Decimal(str(r[1])), str(r[2])) for r in rows}


# Servicio principal
async def validar_insumos_y_precios(
    params: ValidacionParametros, db: AsyncSession
) -> ResultadoValidacion:
    """
    Valida recetas e insumos previo al cálculo de costos.

    Modo estricto (default):
      - Si hay errores (faltan precios, receta vacía, cantidad <= 0, ubicación inválida),
        ok=False, errors poblado, recetas vacías (no se devuelven parciales), warnings vacío.

    Modo tolerante (allow_missing_prices=True):
      - ok=True siempre; errors=[], se agregan warnings y los insumos sin precio llevan precio_unitario=None y moneda=None.
    """
    correlation_summary: dict[str, Any] = {
        "fecha": params.fecha.isoformat(),
        "ubicacion_codigo": params.ubicacion_codigo,
        "recetas": params.receta_codigos,
        "tolerante": params.allow_missing_prices,
    }

    issues: list[ValidationIssue] = []

    # Validación básica de entrada
    if not params.receta_codigos:
        issues.append(
            ValidationIssue(
                code="RECETAS_VACIAS",
                severity="ERROR",
                context={"ubicacion_codigo": params.ubicacion_codigo},
                message="La lista de recetas está vacía.",
            )
        )

    # Ubicación
    location = await get_ubicacion_by_codigo(db, params.ubicacion_codigo)
    if location is None:
        issues.append(
            ValidationIssue(
                code="UBICACION_INVALIDA",
                severity="ERROR",
                context={"ubicacion_codigo": params.ubicacion_codigo},
                message=f"Ubicación inválida: {params.ubicacion_codigo}",
            )
        )

    # En estricto, cortar temprano por errores de entrada/ubicación
    strict_mode = not params.allow_missing_prices
    if strict_mode and any(i.severity == "ERROR" for i in issues):
        for i in issues:
            level = logger.error if i.severity == "ERROR" else logger.warning
            level(i.message, extra={"code": i.code, **i.context})
        return ResultadoValidacion(
            ok=False,
            recetas=[],
            warnings=[],
            errors=[i.message for i in issues if i.severity == "ERROR"],
        )

    # Cargar recetas e insumos activos
    recetas_map = await get_recetas_with_insumos(db, params.receta_codigos, params.fecha)

    # Validar cantidades y existencia de al menos un insumo por receta
    insumo_ids: set[int] = set()
    for receta_code, items in recetas_map.items():
        if not items:
            msg = f"La receta {receta_code} no contiene insumos."
            if strict_mode:
                issues.append(
                    ValidationIssue(
                        code="RECETA_SIN_INSUMOS",
                        severity="ERROR",
                        context={"receta_codigo": receta_code},
                        message=msg,
                    )
                )
            else:
                issues.append(
                    ValidationIssue(
                        code="RECETA_SIN_INSUMOS",
                        severity="WARNING",
                        context={"receta_codigo": receta_code},
                        message=msg,
                    )
                )

        for it in items:
            qty = Decimal(str(it["quantity"]))
            if qty <= 0:
                issues.append(
                    ValidationIssue(
                        code="CANTIDAD_INVALIDA",
                        severity="ERROR" if strict_mode else "WARNING",
                        context={
                            "receta_codigo": receta_code,
                            "insumo_codigo": it["insumo_code"],
                            "cantidad": str(qty),
                        },
                        message=(
                            f"Cantidad inválida para insumo {it['insumo_code']} en {receta_code}: {qty}"
                        ),
                    )
                )
            insumo_ids.add(int(it["insumo_id"]))

    # En estricto, no devolver parciales si hay errores a este punto
    if strict_mode and any(i.severity == "ERROR" for i in issues):
        for i in issues:
            level = logger.error if i.severity == "ERROR" else logger.warning
            level(i.message, extra={"code": i.code, **i.context})
        return ResultadoValidacion(
            ok=False,
            recetas=[],
            warnings=[],
            errors=[i.message for i in issues if i.severity == "ERROR"],
        )

    # Obtener precios vigentes en un solo roundtrip
    precios = await get_precios_vigentes(db, sorted(insumo_ids), params.ubicacion_codigo, params.fecha)

    # Construir resultado por receta
    recetas_validadas: list[RecetaValidada] = []
    top_warnings: list[str] = []

    for receta_code in params.receta_codigos:
        items = recetas_map.get(receta_code, [])
        insumos_validados: list[InsumoValidado] = []

        missing_count = 0
        for it in items:
            insumo_id = int(it["insumo_id"])
            insumo_code = it["insumo_code"]
            qty = Decimal(str(it["quantity"]))
            unit = it["unit"]

            warnings_local: list[str] = []
            precio_unitario: Decimal | None = None
            moneda: str | None = None

            precio_info = precios.get(insumo_id)
            if precio_info is None:
                # Precio faltante
                msg = (
                    f"Falta precio para el insumo {insumo_code} en {params.ubicacion_codigo} al {params.fecha.isoformat()}"
                )
                if strict_mode:
                    issues.append(
                        ValidationIssue(
                            code="PRECIO_FALTANTE",
                            severity="ERROR",
                            context={
                                "receta_codigo": receta_code,
                                "insumo_codigo": insumo_code,
                                "ubicacion_codigo": params.ubicacion_codigo,
                                "fecha": params.fecha.isoformat(),
                            },
                            message=msg,
                        )
                    )
                else:
                    issues.append(
                        ValidationIssue(
                            code="PRECIO_FALTANTE",
                            severity="WARNING",
                            context={
                                "receta_codigo": receta_code,
                                "insumo_codigo": insumo_code,
                                "ubicacion_codigo": params.ubicacion_codigo,
                                "fecha": params.fecha.isoformat(),
                            },
                            message=msg,
                        )
                    )
                    warnings_local.append(msg)
                    missing_count += 1
            else:
                precio, curr = precio_info
                if not curr:
                    msg = (
                        f"Moneda faltante para el insumo {insumo_code} en {params.ubicacion_codigo} al {params.fecha.isoformat()}"
                    )
                    if strict_mode:
                        issues.append(
                            ValidationIssue(
                                code="MONEDA_FALTANTE",
                                severity="ERROR",
                                context={
                                    "receta_codigo": receta_code,
                                    "insumo_codigo": insumo_code,
                                    "ubicacion_codigo": params.ubicacion_codigo,
                                    "fecha": params.fecha.isoformat(),
                                },
                                message=msg,
                            )
                        )
                    else:
                        issues.append(
                            ValidationIssue(
                                code="MONEDA_FALTANTE",
                                severity="WARNING",
                                context={
                                    "receta_codigo": receta_code,
                                    "insumo_codigo": insumo_code,
                                    "ubicacion_codigo": params.ubicacion_codigo,
                                    "fecha": params.fecha.isoformat(),
                                },
                                message=msg,
                            )
                        )
                        warnings_local.append(msg)
                        # Tolerante: anular precio si no hay moneda
                        precio_unitario = None
                        moneda = None
                else:
                    precio_unitario = precio
                    moneda = curr

            insumos_validados.append(
                InsumoValidado(
                    insumo_codigo=insumo_code,
                    cantidad=qty,
                    unidad=unit,
                    precio_unitario=precio_unitario,
                    moneda=moneda,
                    warnings=warnings_local,
                )
            )

        receta_warnings: list[str] = []
        if missing_count > 0:
            msg = f"{missing_count} insumo(s) sin precio en {receta_code}"
            receta_warnings.append(msg)
            top_warnings.append(msg)

        recetas_validadas.append(
            RecetaValidada(receta_codigo=receta_code, insumos=insumos_validados, warnings=receta_warnings)
        )

    # Logging de issues
    for i in issues:
        level = logger.error if i.severity == "ERROR" else logger.warning
        level(i.message, extra={"code": i.code, **i.context})

    if strict_mode and any(i.severity == "ERROR" for i in issues):
        return ResultadoValidacion(
            ok=False,
            recetas=[],
            warnings=[],
            errors=[i.message for i in issues if i.severity == "ERROR"],
        )

    return ResultadoValidacion(
        ok=True,
        recetas=recetas_validadas,
        warnings=top_warnings,
        errors=[],
    )

