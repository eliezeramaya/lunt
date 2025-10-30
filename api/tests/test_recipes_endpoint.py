from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.models import Concept, ConceptRecipe, Insumo, InsumoPrice
from api.models.users_locations import Location


@pytest.mark.asyncio
async def test_endpoint_recetas_preview_aggregate(db_session):
    # Seed
    await db_session.merge(Location(code="CDMX", name="Ciudad de México"))
    c = Concept(code="MURO-BLOCK", description="Muro", unit="m2")
    i1 = Insumo(code="ARE-020", description="Arena", unit="m3", category="material")
    await db_session.merge(c)
    await db_session.merge(i1)
    await db_session.flush()
    await db_session.merge(
        ConceptRecipe(
            concept_id=c.id,
            insumo_id=i1.id,
            quantity=0.8,
            valid_from=date(2024, 1, 1),
            variant_id="std",
            variant_label="estandar",
            recipe_code="REC-MB-STD",
            active=True,
        )
    )
    await db_session.merge(
        ConceptRecipe(
            concept_id=c.id,
            insumo_id=i1.id,
            quantity=0.9,
            valid_from=date(2024, 1, 1),
            variant_id="ref",
            variant_label="reforzada",
            recipe_code="REC-MB-REF",
            active=True,
        )
    )
    await db_session.merge(
        InsumoPrice(
            insumo_id=i1.id, location_code="CDMX", price=Decimal("250.00"), currency="MXN", valid_from=date(2025, 8, 1)
        )
    )
    await db_session.commit()

    from api.services import db as db_module

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[db_module.get_db] = _override_get_db

    client = TestClient(app)
    resp = client.post(
        "/v1/motor/recetas/preview",
        json={
            "concepto_codigo": "MURO-BLOCK",
            "fecha": "2025-09-01",
            "ubicacion_codigo": "CDMX",
            "selection_mode": "aggregate",
        },
    )
    assert resp.status_code == 200
    assert "X-Correlation-Id" in resp.headers
    data = resp.json()
    assert data["selection_mode"] == "aggregate"
    assert len(data["variants_considered"]) == 2
    assert data["insumos"][0]["cantidad"] == 1.7

