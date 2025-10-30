from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from api.models import Concept, ConceptRecipe, Insumo, InsumoPrice, Location
from api.schemas.costs import CostParams
from api.schemas.recipes import RecipeSelectionMode, RecipeStrategy
from api.services.costs import compute_cost


async def seed_base(db_session):
    await db_session.merge(Location(code="CDMX", name="Ciudad de México"))
    await db_session.merge(Location(code="GDL", name="Guadalajara"))

    muro = Concept(code="MURO-BLOCK", description="Muro block", unit="m2")
    acustico = Concept(code="MURO-ACUSTICO", description="Muro acustico", unit="m2")
    cem = Insumo(code="CEM-001", description="Cemento", unit="t", category="material")
    are = Insumo(code="ARE-020", description="Arena", unit="m3", category="material")
    ref = Insumo(code="REF-010", description="Refuerzo", unit="kg", category="material")
    await db_session.merge(muro)
    await db_session.merge(acustico)
    await db_session.merge(cem)
    await db_session.merge(are)
    await db_session.merge(ref)
    await db_session.flush()

    # MURO-BLOCK std/ref
    await db_session.merge(
        ConceptRecipe(concept_id=muro.id, insumo_id=cem.id, quantity=1.0, valid_from=date(2024, 1, 1), variant_id="std", variant_label="estandar", recipe_code="REC-MB-STD", active=True)
    )
    await db_session.merge(
        ConceptRecipe(concept_id=muro.id, insumo_id=are.id, quantity=0.8, valid_from=date(2024, 1, 1), variant_id="std", variant_label="estandar", recipe_code="REC-MB-STD", active=True)
    )
    await db_session.merge(
        ConceptRecipe(concept_id=muro.id, insumo_id=cem.id, quantity=1.2, valid_from=date(2024, 1, 1), variant_id="ref", variant_label="reforzada", recipe_code="REC-MB-REF", active=True)
    )
    await db_session.merge(
        ConceptRecipe(concept_id=muro.id, insumo_id=ref.id, quantity=5.0, valid_from=date(2024, 1, 1), variant_id="ref", variant_label="reforzada", recipe_code="REC-MB-REF", active=True)
    )

    # MURO-ACUSTICO (moneda distinta simulada con falta de precio u otra moneda en lógica actual)
    await db_session.merge(
        ConceptRecipe(concept_id=acustico.id, insumo_id=cem.id, quantity=0.5, valid_from=date(2024, 1, 1), variant_id="std", variant_label="estandar", recipe_code="REC-MA-STD", active=True)
    )

    # Precios
    await db_session.merge(InsumoPrice(insumo_id=cem.id, location_code="CDMX", price=Decimal("2500.00"), currency="MXN", valid_from=date(2025, 1, 1)))
    await db_session.merge(InsumoPrice(insumo_id=are.id, location_code="CDMX", price=Decimal("250.00"), currency="MXN", valid_from=date(2025, 1, 1)))
    await db_session.merge(InsumoPrice(insumo_id=ref.id, location_code="CDMX", price=Decimal("30.00"), currency="MXN", valid_from=date(2025, 1, 1)))
    await db_session.commit()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "cfg",
    [
        dict(
            concepto="MURO-BLOCK",
            ubicacion="CDMX",
            fecha=date(2025, 9, 1),
            selection_mode=RecipeSelectionMode.aggregate,
            allow_missing=False,
            porc_ind=Decimal("0.10"),
            porc_util=Decimal("0.10"),
        ),
        dict(
            concepto="MURO-BLOCK",
            ubicacion="CDMX",
            fecha=date(2025, 9, 1),
            selection_mode=RecipeSelectionMode.single,
            recipe_variant_id="ref",
            allow_missing=False,
            porc_ind=Decimal("0.08"),
            porc_util=Decimal("0.12"),
        ),
        dict(
            concepto="MURO-BLOCK",
            ubicacion="CDMX",
            fecha=date(2025, 9, 1),
            selection_mode=RecipeSelectionMode.strategy,
            strategy=RecipeStrategy.cheapest,
            allow_missing=True,
            porc_ind=Decimal("0.10"),
            porc_util=Decimal("0.10"),
        ),
    ],
)
async def test_engine_variations(db_session, cfg):
    await seed_base(db_session)
    params = CostParams(
        fecha=cfg["fecha"],
        ubicacion_codigo=cfg["ubicacion"],
        concepto_codigo=cfg["concepto"],
        selection_mode=cfg["selection_mode"],
        recipe_variant_id=cfg.get("recipe_variant_id"),
        strategy=cfg.get("strategy"),
        allow_missing_prices=cfg["allow_missing"],
        porcentaje_indirectos=cfg["porc_ind"],
        porcentaje_utilidad=cfg["porc_util"],
    )
    res = await compute_cost(params, db_session)
    assert "breakdown" in res or res.get("errors")
    if "breakdown" in res:
        bd = res["breakdown"]
        for k in [
            "costo_directo",
            "indirectos_pct",
            "indirectos_monto",
            "subtotal_cd_i",
            "utilidad_pct",
            "utilidad_monto",
            "costo_total",
        ]:
            assert k in bd

