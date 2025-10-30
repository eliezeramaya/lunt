from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from api.models import Insumo, InsumoPrice
from api.models.users_locations import Location
from api.schemas.validacion import ValidacionParametros
from api.services.validacion_insumos_precios import get_precios_vigentes, validar_insumos_y_precios


def unique_sorted_dates(max_items: int = 5):
    # Generate strictly increasing offsets (days) <= 30
    return (
        st.lists(st.integers(min_value=1, max_value=30), min_size=1, max_size=max_items, unique=True)
        .map(sorted)
        .map(lambda offs: [date(2025, 8, 1) + timedelta(days=o) for o in offs])
    )


@pytest.mark.asyncio
@settings(max_examples=25)
@given(ds=unique_sorted_dates(5), prices=st.lists(st.decimals(min_value=Decimal("1.00"), max_value=Decimal("999.99"), places=2), min_size=1, max_size=5))
async def test_precio_vigente_property(db_session, ds, prices):
    # Align lengths
    n = min(len(ds), len(prices))
    ds = ds[:n]
    prices = prices[:n]

    # Setup
    db_session.add(Location(code="CDMX", name="Ciudad de México"))
    ins = Insumo(code="MAT-XYZ", description="X", unit="pza", category="material")
    db_session.add(ins)
    await db_session.flush()

    # Insert price history with various valid_from values (no valid_until)
    for d, p in zip(ds, prices):
        db_session.add(
            InsumoPrice(
                insumo_id=ins.id, location_code="CDMX", price=Decimal(str(p)), currency="MXN", valid_from=d
            )
        )
    await db_session.commit()

    # Verificar que get_precios_vigentes elige el más reciente <= fecha objetivo
    prices_map = await get_precios_vigentes(db_session, [ins.id], "CDMX", ds[-1])
    assert ins.id in prices_map
    latest_price = prices_map[ins.id][0]
    # El precio esperado es el asociado a la última fecha de ds
    assert latest_price == Decimal(str(prices[-1]))

    # Build a minimal scenario with a dummy recipe code but we won't rely on recipe mapping here; instead
    # the service will flag "sin insumos"; run tolerant to proceed and fetch prices anyway
    params = ValidacionParametros(
        fecha=ds[-1], ubicacion_codigo="CDMX", receta_codigos=["REC-DUMMY"], allow_missing_prices=True
    )
    res = await validar_insumos_y_precios(params, db_session)

    # If there are no recipes, service returns empty insumos for recipe; the core property (row_number selection)
    # is indirectly tested by ensuring no error occurs. We also test direct latest date correctness by querying via service would be complex here.
    # Therefore, assert that the service ran and produced ok=True with warnings about no insumos.
    assert res.ok is True
    assert res.recetas[0].insumos == []
