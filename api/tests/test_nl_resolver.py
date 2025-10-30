from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.models import Concept, ConceptRecipe, Insumo, InsumoPrice
from api.models.users_locations import Location


@pytest.mark.asyncio
async def test_nl_bypass_with_concept_code(db_session, monkeypatch):
    await db_session.merge(Location(code="CDMX", name="Ciudad de México"))
    c = Concept(code="MURO-BLOCK", description="Muro de block", unit="m2")
    i = Insumo(code="ARE-020", description="Arena", unit="m3", category="material")
    await db_session.merge(c)
    await db_session.merge(i)
    await db_session.flush()
    await db_session.merge(ConceptRecipe(concept_id=c.id, insumo_id=i.id, quantity=1.0, valid_from=date(2024, 1, 1), variant_id="std", active=True))
    await db_session.merge(InsumoPrice(insumo_id=i.id, location_code="CDMX", price=Decimal("100.00"), currency="MXN", valid_from=date(2025, 8, 1)))
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
            "concepto_codigo": "MURO-BLOCK",
            "description": "muro block reforzado",
            "porcentaje_indirectos": 0.10,
            "porcentaje_utilidad": 0.10,
        },
    )
    assert resp.status_code == 422
    data = resp.json()
    assert data["concepto_codigo"] == "MURO-BLOCK"
    assert "resolution" in data["meta"]
    assert data["meta"]["resolution"]["backend"] == "bypass"


@pytest.mark.asyncio
async def test_nl_resolution_low_confidence(db_session, monkeypatch):
    await db_session.merge(Location(code="CDMX", name="Ciudad de México"))
    # Only create a concept that won't match the description, force threshold high
    c = Concept(code="ALGO", description="Algo distinto", unit="m2")
    await db_session.merge(c)
    await db_session.commit()

    from api.services import db as db_module
    async def _override_get_db():
        yield db_session
    app.dependency_overrides[db_module.get_db] = _override_get_db
    client = TestClient(app)

    monkeypatch.setenv("NL_SCORE_THRESHOLD", "0.95")

    resp = client.post(
        "/v1/motor/costos/preview",
        json={
            "fecha": "2025-09-01",
            "ubicacion_codigo": "CDMX",
            "description": "texto que no coincide",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["errors"]
    assert "resolution" in data.get("meta", {})


@pytest.mark.asyncio
async def test_nl_resolution_ok(db_session, monkeypatch):
    await db_session.merge(Location(code="CDMX", name="Ciudad de México"))
    c = Concept(code="MURO-BLOCK", description="Muro de block reforzado con castillos", unit="m2")
    i = Insumo(code="ARE-020", description="Arena", unit="m3", category="material")
    await db_session.merge(c)
    await db_session.merge(i)
    await db_session.flush()
    await db_session.merge(ConceptRecipe(concept_id=c.id, insumo_id=i.id, quantity=1.0, valid_from=date(2024, 1, 1), variant_id="std", active=True))
    await db_session.merge(InsumoPrice(insumo_id=i.id, location_code="CDMX", price=Decimal("100.00"), currency="MXN", valid_from=date(2025, 8, 1)))
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
            "description": "muro block reforzado con castillos",
            "porcentaje_indirectos": 0.10,
            "porcentaje_utilidad": 0.10,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["concepto_codigo"] == "MURO-BLOCK"
    assert "resolution" in data["meta"]
    assert data["meta"]["resolution"]["backend"] in ("qdrant", "bypass")
    # Confidence feedback exists
    assert "confidence_score" in data["meta"]["resolution"]
    assert 0.0 <= data["meta"]["resolution"]["confidence_score"] <= 1.0
