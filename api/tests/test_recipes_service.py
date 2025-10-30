from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from api.models import Concept, ConceptRecipe, Insumo, InsumoPrice
from api.models.users_locations import Location
from api.schemas.recipes import RecipeRequestParams, RecipeSelectionMode, RecipeStrategy
from api.services.recipes import get_recipes_for_concept


async def _seed_variants(db_session):
    await db_session.merge(Location(code="CDMX", name="Ciudad de México"))
    concept = Concept(code="MURO-BLOCK", description="Muro de block", unit="m2")
    await db_session.merge(concept)
    ins_cem = Insumo(code="CEM-001", description="Cemento", unit="t", category="material")
    ins_are = Insumo(code="ARE-020", description="Arena", unit="m3", category="material")
    ins_ref = Insumo(code="REF-010", description="Refuerzo", unit="kg", category="material")
    await db_session.merge(ins_cem)
    await db_session.merge(ins_are)
    await db_session.merge(ins_ref)
    await db_session.flush()

    # Variante estandar (std)
    await db_session.merge(
        ConceptRecipe(
            concept_id=concept.id,
            insumo_id=ins_cem.id,
            quantity=1.2,
            valid_from=date(2024, 1, 1),
            variant_id="std",
            variant_label="estandar",
            recipe_code="REC-MB-STD",
            active=True,
        )
    )
    await db_session.merge(
        ConceptRecipe(
            concept_id=concept.id,
            insumo_id=ins_are.id,
            quantity=0.8,
            valid_from=date(2024, 1, 1),
            variant_id="std",
            variant_label="estandar",
            recipe_code="REC-MB-STD",
            active=True,
        )
    )

    # Variante reforzada (ref)
    await db_session.merge(
        ConceptRecipe(
            concept_id=concept.id,
            insumo_id=ins_cem.id,
            quantity=1.4,
            valid_from=date(2024, 1, 1),
            variant_id="ref",
            variant_label="reforzada",
            recipe_code="REC-MB-REF",
            active=True,
        )
    )
    await db_session.merge(
        ConceptRecipe(
            concept_id=concept.id,
            insumo_id=ins_are.id,
            quantity=0.9,
            valid_from=date(2024, 1, 1),
            variant_id="ref",
            variant_label="reforzada",
            recipe_code="REC-MB-REF",
            active=True,
        )
    )
    await db_session.merge(
        ConceptRecipe(
            concept_id=concept.id,
            insumo_id=ins_ref.id,
            quantity=5.0,
            valid_from=date(2024, 1, 1),
            variant_id="ref",
            variant_label="reforzada",
            recipe_code="REC-MB-REF",
            active=True,
        )
    )

    # Precios: ARE y REF tienen precio; CEM sin precio para probar warnings
    await db_session.merge(
        InsumoPrice(
            insumo_id=ins_are.id, location_code="CDMX", price=Decimal("250.00"), currency="MXN", valid_from=date(2025, 8, 1)
        )
    )
    await db_session.merge(
        InsumoPrice(
            insumo_id=ins_ref.id, location_code="CDMX", price=Decimal("30.00"), currency="MXN", valid_from=date(2025, 8, 1)
        )
    )
    await db_session.commit()


@pytest.mark.asyncio
async def test_aggregate_mode_with_variants(db_session):
    await _seed_variants(db_session)
    params = RecipeRequestParams(
        concepto_codigo="MURO-BLOCK",
        fecha=date(2025, 9, 1),
        ubicacion_codigo="CDMX",
        selection_mode=RecipeSelectionMode.aggregate,
        allow_missing_prices=True,
    )
    res = await get_recipes_for_concept(params, db_session)
    assert res.selection_mode == RecipeSelectionMode.aggregate
    assert len(res.variants_considered) == 2
    # Insumos agregados deben incluir multiple y sumar cantidades
    agg = {i.insumo_codigo: i for i in res.insumos}
    assert agg["ARE-020"].cantidad == Decimal("1.7")  # 0.8 + 0.9
    assert agg["ARE-020"].source_variant_id == "multiple"
    # Falta precio para CEM-001 -> precio_unitario null
    assert agg["CEM-001"].precio_unitario is None
    assert any("sin precio" in w.lower() for w in res.warnings)


@pytest.mark.asyncio
async def test_single_variant_selection(db_session):
    await _seed_variants(db_session)
    params = RecipeRequestParams(
        concepto_codigo="MURO-BLOCK",
        fecha=date(2025, 9, 1),
        ubicacion_codigo="CDMX",
        selection_mode=RecipeSelectionMode.single,
        recipe_variant_id="ref",
        allow_missing_prices=True,
    )
    res = await get_recipes_for_concept(params, db_session)
    assert res.used_variant_id == "ref"
    codes = {i.insumo_codigo for i in res.insumos}
    assert "REF-010" in codes  # solo en reforzada


@pytest.mark.asyncio
async def test_strategy_cheapest(db_session):
    await _seed_variants(db_session)
    params = RecipeRequestParams(
        concepto_codigo="MURO-BLOCK",
        fecha=date(2025, 9, 1),
        ubicacion_codigo="CDMX",
        selection_mode=RecipeSelectionMode.strategy,
        strategy=RecipeStrategy.cheapest,
        allow_missing_prices=True,
    )
    res = await get_recipes_for_concept(params, db_session)
    assert res.used_strategy == RecipeStrategy.cheapest
    assert res.used_variant_id in {"std", "ref"}


@pytest.mark.asyncio
async def test_variant_not_found_error(db_session):
    await _seed_variants(db_session)
    params = RecipeRequestParams(
        concepto_codigo="MURO-BLOCK",
        fecha=date(2025, 9, 1),
        ubicacion_codigo="CDMX",
        selection_mode=RecipeSelectionMode.single,
        recipe_variant_id="nope",
    )
    res = await get_recipes_for_concept(params, db_session)
    assert any("VARIANTE_NO_ENCONTRADA" in e for e in res.errors)

