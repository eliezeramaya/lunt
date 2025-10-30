from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.concepts import Concept, ConceptRecipe
from api.models.insumos import Insumo
from api.models.users_locations import Location
from api.schemas.recipes import (
    RecipePreview,
    RecipePreviewInsumo,
    RecipePreviewVariant,
    RecipeRequestParams,
    RecipeSelectionMode,
    RecipeStrategy,
)
from api.services.logging_config import get_logger
from api.services.validacion_insumos_precios import get_precios_vigentes


logger = get_logger(__name__)


@dataclass
class _VariantItem:
    receta_id: int
    variant_id: str
    variant_label: str | None
    recipe_code: str | None
    insumo_id: int
    insumo_code: str
    unit: str
    quantity: Decimal


async def _get_location(db: AsyncSession, code: str) -> Location | None:
    q = select(Location).where(Location.code == code)
    return (await db.execute(q)).scalar_one_or_none()


async def _load_variants(
    db: AsyncSession, concepto_codigo: str, fecha: date
) -> dict[str, list[_VariantItem]]:
    """Carga las variantes activas de un concepto a la fecha con sus insumos."""
    q = (
        select(
            ConceptRecipe.id.label("receta_id"),
            ConceptRecipe.variant_id,
            ConceptRecipe.variant_label,
            ConceptRecipe.recipe_code,
            Concept.code.label("concept_code"),
            Insumo.id.label("insumo_id"),
            Insumo.code.label("insumo_code"),
            Insumo.unit.label("unit"),
            ConceptRecipe.quantity.label("quantity"),
        )
        .join(Concept, Concept.id == ConceptRecipe.concept_id)
        .join(Insumo, Insumo.id == ConceptRecipe.insumo_id)
        .where(
            and_(
                Concept.code == concepto_codigo,
                ConceptRecipe.active.is_(True),
                ConceptRecipe.valid_from <= fecha,
                or_(ConceptRecipe.valid_until.is_(None), ConceptRecipe.valid_until >= fecha),
            )
        )
    )
    rows = (await db.execute(q)).mappings().all()
    variants: dict[str, list[_VariantItem]] = defaultdict(list)
    for r in rows:
        variants[r["variant_id"]].append(
            _VariantItem(
                receta_id=int(r["receta_id"]),
                variant_id=str(r["variant_id"]),
                variant_label=(r["variant_label"] or r["variant_id"]),
                recipe_code=r["recipe_code"],
                insumo_id=int(r["insumo_id"]),
                insumo_code=str(r["insumo_code"]),
                unit=str(r["unit"]),
                quantity=Decimal(str(r["quantity"])),
            )
        )
    return variants


def _variant_label(items: list[_VariantItem]) -> tuple[str, str | None]:
    vid = items[0].variant_id
    label = items[0].variant_label or vid
    return vid, label


def _variant_recipe_code(items: list[_VariantItem]) -> str | None:
    for it in items:
        if it.recipe_code:
            return it.recipe_code
    return None


def _sum_cost_for_variant(
    items: list[_VariantItem], price_map: dict[int, tuple[Decimal, str]]
) -> tuple[Decimal | None, list[str], int, set[str]]:
    """Suma costo de una variante. Retorna (cost, warnings, missing_count, currencies)."""
    cost = Decimal("0")
    warnings: list[str] = []
    missing = 0
    currencies: set[str] = set()
    for it in items:
        p = price_map.get(it.insumo_id)
        if p is None:
            missing += 1
            continue
        price, currency = p
        currencies.add(currency)
        cost += price * it.quantity
    if len(currencies) > 1:
        warnings.append("MONEDA_INCONSISTENTE: múltiples monedas en variante")
    return (cost if missing == 0 else cost, warnings, missing, currencies)


def _aggregate_insumos(
    selected_variants: list[list[_VariantItem]],
    price_map: dict[int, tuple[Decimal, str]],
    allow_missing_prices: bool,
) -> tuple[list[RecipePreviewInsumo], list[str]]:
    agg: dict[tuple[str, str], Decimal] = defaultdict(lambda: Decimal("0"))
    warnings: list[str] = []
    insumo_present: dict[tuple[str, str], bool] = {}

    for items in selected_variants:
        for it in items:
            key = (it.insumo_code, it.unit)
            agg[key] += it.quantity
            insumo_present[key] = insumo_present.get(key, False) or (it.insumo_id in price_map)

    out: list[RecipePreviewInsumo] = []
    for (code, unit), qty in agg.items():
        # Any item among variants can be used to lookup price via insumo_code -> id is not available here.
        # Since unit price is per insumo regardless of variant, choose price by searching any it with same code.
        # Build a small resolver map by code
        price: Decimal | None = None
        currency: str | None = None
        price_found = False
        for items in selected_variants:
            for it in items:
                if it.insumo_code == code:
                    p = price_map.get(it.insumo_id)
                    if p is not None:
                        price_found = True
                        price, currency = p
                        break
            if price_found:
                break

        if not price_found:
            if not allow_missing_prices:
                # handled by caller using errors; here leave None
                pass
            else:
                warnings.append(f"Falta precio para el insumo {code}")

        out.append(
            RecipePreviewInsumo(
                insumo_codigo=code,
                cantidad=qty,
                unidad=unit,
                precio_unitario=price if price_found else None,
                moneda=currency if price_found else None,
                source_variant_id="multiple",
                warnings=(
                    [f"Falta precio para el insumo {code}"] if allow_missing_prices and not price_found else []
                ),
            )
        )

    if any(i.precio_unitario is None for i in out):
        warnings.append("COSTO_PARCIAL_AGREGADO: insumos sin precio en variantes agregadas")

    return out, warnings


async def get_recipes_for_concept(params: RecipeRequestParams, db: AsyncSession) -> RecipePreview:
    # Validación básica
    errors: list[str] = []
    warnings: list[str] = []

    loc = await _get_location(db, params.ubicacion_codigo)
    if loc is None:
        return RecipePreview(
            concepto_codigo=params.concepto_codigo,
            selection_mode=params.selection_mode,
            used_variant_id=None,
            used_strategy=None,
            variants_considered=[],
            insumos=[],
            warnings=[],
            errors=[f"Ubicación inválida: {params.ubicacion_codigo}"],
        )

    variants = await _load_variants(db, params.concepto_codigo, params.fecha)
    if not variants:
        return RecipePreview(
            concepto_codigo=params.concepto_codigo,
            selection_mode=params.selection_mode,
            used_variant_id=None,
            used_strategy=None,
            variants_considered=[],
            insumos=[],
            warnings=[],
            errors=[
                f"SIN_VARIANTES_PARA_CONCEPTO {params.concepto_codigo} en {params.ubicacion_codigo} al {params.fecha.isoformat()}"
            ],
        )

    # Precios: juntar todos los insumo_ids de todas las variantes en una sola consulta
    all_insumo_ids: set[int] = set()
    for items in variants.values():
        for it in items:
            all_insumo_ids.add(it.insumo_id)
    price_map = await get_precios_vigentes(db, sorted(all_insumo_ids), params.ubicacion_codigo, params.fecha)

    # Armar variants_considered con costos
    considered: list[RecipePreviewVariant] = []
    variant_costs: dict[str, tuple[Decimal | None, int]] = {}
    variant_codes: dict[str, str | None] = {}
    for vid, items in variants.items():
        cost, warns, missing, currencies = _sum_cost_for_variant(items, price_map)
        if warns:
            warnings.extend(warns)
        if missing > 0 and not params.allow_missing_prices:
            errors.append(
                f"Faltan {missing} precio(s) en variante {vid} para {params.concepto_codigo} en {params.ubicacion_codigo} al {params.fecha.isoformat()}"
            )
        variant_codes[vid] = _variant_recipe_code(items)
        considered.append(
            RecipePreviewVariant(
                variant_id=vid,
                variant_label=_variant_label(items)[1] or vid,
                receta_codigo=variant_codes[vid],
                aggregated_cost=(None if (missing > 0 and not params.allow_missing_prices) else cost),
                warnings=(
                    [f"Costo parcial en '{vid}' por {missing} insumo(s) sin precio"]
                    if missing > 0 and params.allow_missing_prices
                    else []
                ),
            )
        )
        variant_costs[vid] = (cost, missing)

    # Cortar por errores estrictos de precios
    if errors and not params.allow_missing_prices:
        return RecipePreview(
            concepto_codigo=params.concepto_codigo,
            selection_mode=params.selection_mode,
            used_variant_id=None,
            used_strategy=None,
            variants_considered=considered,
            insumos=[],
            warnings=warnings,
            errors=errors,
        )

    # Selección según modo
    selected_variants: list[list[_VariantItem]] = []
    used_variant_id: str | None = None
    used_strategy = None

    if params.selection_mode == RecipeSelectionMode.aggregate:
        selected_variants = list(variants.values())
    elif params.selection_mode == RecipeSelectionMode.single:
        if not params.recipe_variant_id or params.recipe_variant_id not in variants:
            return RecipePreview(
                concepto_codigo=params.concepto_codigo,
                selection_mode=params.selection_mode,
                used_variant_id=None,
                used_strategy=None,
                variants_considered=considered,
                insumos=[],
                warnings=warnings,
                errors=[f"VARIANTE_NO_ENCONTRADA {params.recipe_variant_id or ''}"],
            )
        used_variant_id = params.recipe_variant_id
        selected_variants = [variants[used_variant_id]]
    else:  # strategy
        if not params.strategy:
            return RecipePreview(
                concepto_codigo=params.concepto_codigo,
                selection_mode=params.selection_mode,
                used_variant_id=None,
                used_strategy=None,
                variants_considered=considered,
                insumos=[],
                warnings=warnings,
                errors=["Falta parámetro 'strategy'"],
            )
        # cheapest: ordenar por (missing, cost) asc, tie-breaker por recipe_code asc
        if params.strategy == RecipeStrategy.cheapest:
            def key_fn(vid: str):
                cost, miss = variant_costs[vid]
                # Asegurar clave comparable
                return (miss, cost or Decimal("0"), (variant_codes[vid] or vid))

            best_vid = sorted(variants.keys(), key=key_fn)[0]
            # Empate detection: compare top two
            sv = sorted(variants.keys(), key=key_fn)
            if len(sv) > 1 and key_fn(sv[0]) == key_fn(sv[1]):
                warnings.append("EMPATE_ESTRATEGIA: se desempató por receta_codigo asc")
            used_variant_id = best_vid
            selected_variants = [variants[best_vid]]
            used_strategy = RecipeStrategy.cheapest
        elif params.strategy == RecipeStrategy.latest:
            # No version metadata; usar receta_id desc como proxy
            best_vid = sorted(
                variants.keys(), key=lambda v: max(it.receta_id for it in variants[v]), reverse=True
            )[0]
            used_variant_id = best_vid
            selected_variants = [variants[best_vid]]
            used_strategy = RecipeStrategy.latest
        else:  # strongest placeholder: prefer labels que contengan 'reforz'
            def score(v: str) -> tuple[int, str]:
                lbl = (_variant_label(variants[v])[1] or v).lower()
                return (0 if ("reforz" in lbl or "reforzada" in lbl) else 1, (variant_codes[v] or v))

            best_vid = sorted(variants.keys(), key=score)[0]
            used_variant_id = best_vid
            selected_variants = [variants[best_vid]]
            used_strategy = RecipeStrategy.strongest

    # Construir insumos final
    if params.selection_mode == RecipeSelectionMode.aggregate and len(selected_variants) > 1:
        insumos, warn = _aggregate_insumos(selected_variants, price_map, params.allow_missing_prices)
        warnings.extend(warn)
    else:
        # Solo una variante
        items = selected_variants[0]
        insumos = []
        for it in items:
            p = price_map.get(it.insumo_id)
            if p is None and not params.allow_missing_prices:
                errors.append(
                    f"Falta precio para el insumo {it.insumo_code} en {params.ubicacion_codigo} al {params.fecha.isoformat()}"
                )
            price = p[0] if p else None
            curr = p[1] if p else None
            insumos.append(
                RecipePreviewInsumo(
                    insumo_codigo=it.insumo_code,
                    cantidad=it.quantity,
                    unidad=it.unit,
                    precio_unitario=price,
                    moneda=curr,
                    source_variant_id=it.variant_id,
                    warnings=(
                        [
                            f"Falta precio para el insumo {it.insumo_code} en {params.ubicacion_codigo} al {params.fecha.isoformat()}"
                        ]
                        if (p is None and params.allow_missing_prices)
                        else []
                    ),
                )
            )

    return RecipePreview(
        concepto_codigo=params.concepto_codigo,
        selection_mode=params.selection_mode,
        used_variant_id=used_variant_id,
        used_strategy=used_strategy,
        variants_considered=considered,
        insumos=insumos,
        warnings=warnings,
        errors=errors if not params.allow_missing_prices else [],
    )


# Deprecated wrapper for backward compatibility
async def get_recipe(
    concept_code: str,
    calculation_date: date,
    location_code: str,
    db: AsyncSession,
    allow_missing_prices: bool = False,
    locale: str = "es-MX",
) -> RecipePreview:
    """
    DEPRECATED: Use get_recipes_for_concept with RecipeRequestParams instead.

    This wrapper preserves legacy behavior by delegating to aggregate mode.
    """
    logger.warning(
        "DEPRECATION: get_recipe() is deprecated, use get_recipes_for_concept(...)",
        extra={
            "concept_code": concept_code,
            "location_code": location_code,
            "calculation_date": calculation_date.isoformat(),
        },
    )
    params = RecipeRequestParams(
        concepto_codigo=concept_code,
        fecha=calculation_date,
        ubicacion_codigo=location_code,
        selection_mode=RecipeSelectionMode.aggregate,
        allow_missing_prices=allow_missing_prices,
        locale=locale,
    )
    return await get_recipes_for_concept(params, db)
