from datetime import date
from decimal import Decimal

import pytest

from api.models import Concept, ConceptRecipe, Insumo, InsumoPrice
from api.services.pricing_engine import PricingEngine


@pytest.mark.asyncio
async def test_get_latest_price(db_session):
    """Test getting latest price for an insumo"""
    insumo = Insumo(
        code="TEST-001",
        description="Test Material",
        unit="pza",
        category="material",
    )
    db_session.add(insumo)
    await db_session.flush()

    price = InsumoPrice(
        insumo_id=insumo.id,
        location_code="MX-CDMX",
        price=Decimal("10.50"),
        currency="MXN",
        valid_from=date(2025, 1, 1),
    )
    db_session.add(price)
    await db_session.commit()

    engine = PricingEngine(db_session)
    result = await engine.get_latest_price(
        insumo_id=insumo.id, location_code="MX-CDMX", calculation_date=date(2025, 1, 15)
    )

    assert result == Decimal("10.50")


@pytest.mark.asyncio
async def test_pricing_engine_missing_price(db_session):
    """Test that pricing engine raises error when price not found"""
    insumo = Insumo(
        code="TEST-002",
        description="Test Material No Price",
        unit="pza",
        category="material",
    )
    db_session.add(insumo)
    await db_session.commit()

    engine = PricingEngine(db_session)
    result = await engine.get_latest_price(
        insumo_id=insumo.id, location_code="MX-CDMX", calculation_date=date(2025, 1, 15)
    )

    assert result is None


@pytest.mark.asyncio
async def test_build_base_preview(db_session):
    """Test building a complete preview"""
    concept = Concept(
        code="ALB-001",
        description="Muro de block",
        unit="m2",
        category="albanileria",
    )
    db_session.add(concept)
    await db_session.flush()

    insumo = Insumo(
        code="MAT-001",
        description="Block hueco",
        unit="pza",
        category="material",
    )
    db_session.add(insumo)
    await db_session.flush()

    recipe = ConceptRecipe(
        concept_id=concept.id,
        insumo_id=insumo.id,
        quantity=12.5,
        valid_from=date(2025, 1, 1),
    )
    db_session.add(recipe)

    price = InsumoPrice(
        insumo_id=insumo.id,
        location_code="MX-CDMX",
        price=Decimal("8.50"),
        currency="MXN",
        valid_from=date(2025, 1, 1),
    )
    db_session.add(price)
    await db_session.commit()

    engine = PricingEngine(db_session)
    result = await engine.build_base_preview(
        concept_code="ALB-001",
        location_code="MX-CDMX",
        calculation_date=date(2025, 1, 15),
    )

    assert result["concept_code"] == "ALB-001"
    assert result["costo_directo"] == 106.25
    assert len(result["breakdown"]) == 1
    assert result["precio_unitario"] > result["costo_directo"]
