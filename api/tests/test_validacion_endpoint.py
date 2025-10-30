from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.models import Concept, ConceptRecipe, Insumo, InsumoPrice
from api.models.users_locations import Location


@pytest.mark.asyncio
async def test_endpoint_validar_ok_and_header(db_session, monkeypatch):
    # Seed DB
    await db_session.merge(Location(code="CDMX", name="Ciudad de México"))
    conc = Concept(code="REC-001", description="Receta", unit="m2")
    ins = Insumo(code="ARE-020", description="Arena", unit="m3", category="material")
    await db_session.merge(conc)
    await db_session.merge(ins)
    await db_session.flush()
    await db_session.merge(ConceptRecipe(concept_id=conc.id, insumo_id=ins.id, quantity=0.5, valid_from=date(2024, 1, 1)))
    await db_session.merge(
        InsumoPrice(
            insumo_id=ins.id,
            location_code="CDMX",
            price=Decimal("250.00"),
            currency="MXN",
            valid_from=date(2025, 8, 1),
        )
    )
    await db_session.commit()

    # Use TestClient but inject session via dependency override
    from api.services import db as db_module

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[db_module.get_db] = _override_get_db

    client = TestClient(app)

    resp = client.post(
        "/v1/motor/validar",
        json={
            "fecha": "2025-09-01",
            "ubicacion_codigo": "CDMX",
            "receta_codigos": ["REC-001"],
        },
    )

    assert resp.status_code == 200
    assert "X-Correlation-Id" in resp.headers
    data = resp.json()
    assert data["ok"] is True
    assert data["errors"] == []
    assert data["recetas"][0]["receta_codigo"] == "REC-001"
    assert data["recetas"][0]["insumos"][0]["precio_unitario"] == 250.0

