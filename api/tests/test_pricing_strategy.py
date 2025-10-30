from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from api.models import Concept, ConceptRecipe, Insumo, InsumoPrice
from api.models.users_locations import Location
from api.schemas.costs import CostParams
from api.services.costs import compute_cost
from api.services.pricing_strategies import (
    DefaultPricingStrategy,
    PricingContext,
    PricingEngine,
    PricingResult,
    get_pricing_strategy,
)


@pytest.mark.asyncio
async def test_default_strategy_parity_with_compute_cost(db_session):
    # Seed basic data
    await db_session.merge(Location(code="CDMX", name="Ciudad de México"))
    c = Concept(code="TEST-C", description="Desc", unit="m2")
    i = Insumo(code="MAT-1", description="Mat", unit="u", category="material")
    await db_session.merge(c)
    await db_session.merge(i)
    await db_session.flush()
    await db_session.merge(
        ConceptRecipe(
            concept_id=c.id,
            insumo_id=i.id,
            quantity=2.0,
            valid_from=date(2024, 1, 1),
            variant_id="std",
            active=True,
        )
    )
    await db_session.merge(
        InsumoPrice(
            insumo_id=i.id, location_code="CDMX", price=Decimal("100.00"), currency="MXN", valid_from=date(2025, 8, 1)
        )
    )
    await db_session.commit()

    params = CostParams(
        fecha=date(2025, 9, 1), ubicacion_codigo="CDMX", concepto_codigo="TEST-C", porcentaje_indirectos=Decimal("0.10"), porcentaje_utilidad=Decimal("0.10")
    )
    res = await compute_cost(params, db_session)
    # costo_total debe ser 242.00
    assert res["breakdown"]["costo_total"] == 242.00


def test_get_pricing_strategy_registry():
    s = get_pricing_strategy("default")
    assert isinstance(s, DefaultPricingStrategy)
    with pytest.raises(ValueError):
        get_pricing_strategy("unknown")

