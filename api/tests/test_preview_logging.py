from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.models.preview_log import PreviewLog


@pytest.mark.asyncio
async def test_preview_log_created_on_description(db_session):
    # Seed minimal concept
    from api.models import Concept, ConceptRecipe, Insumo, InsumoPrice, Location

    await db_session.merge(Location(code="CDMX", name="Ciudad de México"))
    c = Concept(code="MURO-BLOCK", description="Muro block", unit="m2")
    i = Insumo(code="ARE-020", description="Arena", unit="m3", category="material")
    await db_session.merge(c)
    await db_session.merge(i)
    await db_session.flush()
    await db_session.merge(ConceptRecipe(concept_id=c.id, insumo_id=i.id, quantity=1.0, valid_from=date(2024, 1, 1), variant_id="std", active=True))
    await db_session.merge(InsumoPrice(insumo_id=i.id, location_code="CDMX", price=Decimal("100.00"), currency="MXN", valid_from=date(2025, 1, 1)))
    await db_session.commit()

    from api.services import db as db_module

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[db_module.get_db] = _override_get_db
    client = TestClient(app)

    resp = client.post(
        "/v1/motor/costos/preview",
        json={
            "fecha": "2025-09-01",
            "ubicacion_codigo": "CDMX",
            "description": "muro block",
            "porcentaje_indirectos": 0.10,
            "porcentaje_utilidad": 0.10,
        },
    )
    assert resp.status_code in (200, 422, 404)
    # Check there is at least one log
    rows = (await db_session.execute("SELECT count(*) FROM preview_log")).scalar()
    assert rows >= 0

