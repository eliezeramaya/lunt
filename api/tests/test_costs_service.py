from __future__ import annotations

from datetime import date
from decimal import Decimal

import os
import pytest

from api.models import Concept, ConceptRecipe, Insumo, InsumoPrice
from api.models.users_locations import Location
from api.schemas.costs import CostParams
from api.schemas.recipes import RecipeSelectionMode
from api.services.costs import compute_cost


async def _seed_basic(db_session):
    await db_session.merge(Location(code="CDMX", name="Ciudad de México"))
    c = Concept(code="MURO-BLOCK", description="Muro", unit="m2")
    mat = Insumo(code="ARE-020", description="Arena", unit="m3", category="material")
    await db_session.merge(c)
    await db_session.merge(mat)
    await db_session.flush()
    await db_session.merge(
        ConceptRecipe(
            concept_id=c.id,
            insumo_id=mat.id,
            quantity=2.0,
            valid_from=date(2024, 1, 1),
            variant_id="std",
            variant_label="estandar",
            active=True,
        )
    )
    await db_session.merge(
        InsumoPrice(
            insumo_id=mat.id, location_code="CDMX", price=Decimal("100.00"), currency="MXN", valid_from=date(2025, 8, 1)
        )
    )
    await db_session.commit()


@pytest.mark.asyncio
async def test_percent_precedence_param_over_env(db_session, monkeypatch):
    await _seed_basic(db_session)
    monkeypatch.setenv("LUNT_DEFAULT_PORC_INDIRECTOS", "0.15")
    monkeypatch.setenv("LUNT_DEFAULT_PORC_UTILIDAD", "0.15")

    params = CostParams(
        fecha=date(2025, 9, 1),
        ubicacion_codigo="CDMX",
        concepto_codigo="MURO-BLOCK",
        porcentaje_indirectos=Decimal("0.08"),
        porcentaje_utilidad=Decimal("0.12"),
    )
    res = await compute_cost(params, db_session)
    assert res["porcentajes_usados"]["indirectos"] == 0.08
    assert res["porcentajes_usados"]["utilidad"] == 0.12


@pytest.mark.asyncio
async def test_percent_from_env_when_missing_params(db_session, monkeypatch):
    await _seed_basic(db_session)
    monkeypatch.setenv("LUNT_DEFAULT_PORC_INDIRECTOS", "0.10")
    monkeypatch.setenv("LUNT_DEFAULT_PORC_UTILIDAD", "0.10")

    params = CostParams(
        fecha=date(2025, 9, 1), ubicacion_codigo="CDMX", concepto_codigo="MURO-BLOCK"
    )
    res = await compute_cost(params, db_session)
    assert res["porcentajes_usados"]["indirectos"] == 0.10
    assert res["porcentajes_usados"]["utilidad"] == 0.10


@pytest.mark.asyncio
async def test_breakdown_values_and_rounding(db_session, monkeypatch):
    await _seed_basic(db_session)
    params = CostParams(
        fecha=date(2025, 9, 1),
        ubicacion_codigo="CDMX",
        concepto_codigo="MURO-BLOCK",
        porcentaje_indirectos=Decimal("0.10"),
        porcentaje_utilidad=Decimal("0.10"),
        output_scale_decimals=2,
    )
    res = await compute_cost(params, db_session)
    bd = res["breakdown"]
    # costo_directo = 2.0 * 100 = 200
    assert bd["costo_directo"] == 200.00
    # indirectos 10% = 20 => subtotal 220, utilidad 10% = 22 => total 242
    assert bd["indirectos_monto"] == 20.00
    assert bd["subtotal_cd_i"] == 220.00
    assert bd["utilidad_monto"] == 22.00
    assert bd["costo_total"] == 242.00


@pytest.mark.asyncio
async def test_strict_mode_aborts_on_missing_price(db_session):
    # seed with no price
    await db_session.merge(Location(code="CDMX", name="Ciudad de México"))
    c = Concept(code="MURO-BLOCK", description="Muro", unit="m2")
    mat = Insumo(code="ARE-020", description="Arena", unit="m3", category="material")
    await db_session.merge(c)
    await db_session.merge(mat)
    await db_session.flush()
    await db_session.merge(
        ConceptRecipe(
            concept_id=c.id,
            insumo_id=mat.id,
            quantity=1.0,
            valid_from=date(2024, 1, 1),
            variant_id="std",
            active=True,
        )
    )
    await db_session.commit()

    params = CostParams(
        fecha=date(2025, 9, 1), ubicacion_codigo="CDMX", concepto_codigo="MURO-BLOCK", allow_missing_prices=False
    )
    res = await compute_cost(params, db_session)
    assert res["errors"]


@pytest.mark.asyncio
async def test_tolerant_mode_partial_cost(db_session):
    # one insumo missing price; allow_missing_prices=True should continue with partial cost and warning
    await db_session.merge(Location(code="CDMX", name="Ciudad de México"))
    c = Concept(code="MURO-BLOCK", description="Muro", unit="m2")
    i1 = Insumo(code="A", description="A", unit="u", category="material")
    i2 = Insumo(code="B", description="B", unit="u", category="material")
    await db_session.merge(c)
    await db_session.merge(i1)
    await db_session.merge(i2)
    await db_session.flush()
    await db_session.merge(ConceptRecipe(concept_id=c.id, insumo_id=i1.id, quantity=1.0, valid_from=date(2024, 1, 1), variant_id="std", active=True))
    await db_session.merge(ConceptRecipe(concept_id=c.id, insumo_id=i2.id, quantity=2.0, valid_from=date(2024, 1, 1), variant_id="std", active=True))
    await db_session.merge(InsumoPrice(insumo_id=i2.id, location_code="CDMX", price=Decimal("50.00"), currency="MXN", valid_from=date(2025, 8, 1)))
    await db_session.commit()

    params = CostParams(
        fecha=date(2025, 9, 1), ubicacion_codigo="CDMX", concepto_codigo="MURO-BLOCK", allow_missing_prices=True
    )
    res = await compute_cost(params, db_session)
    assert "COSTO_PARCIAL" in " ".join(res["warnings"]) or any("sin precio" in w for w in res["warnings"])
    # Direct cost only includes priced insumo: 2 * 50 = 100
    assert res["breakdown"]["costo_directo"] == 100.00

