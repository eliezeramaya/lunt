from __future__ import annotations

import re
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.models import Concept, ConceptRecipe, Insumo, InsumoPrice
from api.models.users_locations import Location


@pytest.mark.asyncio
async def test_metrics_endpoint_and_counters(db_session, monkeypatch):
    # Enable metrics and set whitelist
    monkeypatch.setenv("LUNT_METRICS_ENABLED", "true")
    monkeypatch.setenv("LUNT_METRICS_CONCEPTS_WHITELIST", "MURO-BLOCK")

    # Seed minimal data
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
            quantity=1.0,
            valid_from=date(2024, 1, 1),
            variant_id="std",
            active=True,
        )
    )
    await db_session.merge(
        InsumoPrice(
            insumo_id=i1.id, location_code="CDMX", price=Decimal("100.00"), currency="MXN", valid_from=date(2025, 8, 1)
        )
    )
    await db_session.commit()

    from api.services import db as db_module

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[db_module.get_db] = _override_get_db

    client = TestClient(app)

    # Hit cost preview endpoint to produce metrics
    resp = client.post(
        "/v1/motor/costos/preview",
        json={
            "fecha": "2025-09-01",
            "ubicacion_codigo": "CDMX",
            "concepto_codigo": "MURO-BLOCK",
            "porcentaje_indirectos": 0.10,
            "porcentaje_utilidad": 0.10,
        },
    )
    assert resp.status_code == 200

    # Scrape /metrics
    m = client.get("/metrics")
    assert m.status_code == 200
    text = m.text

    # Check custom metrics exist
    assert "lunt_requests_total" in text
    assert "lunt_request_latency_seconds_bucket" in text
    # Engine metrics as well
    assert "lunt_engine_requests_total" in text
    assert "lunt_engine_compute_seconds_bucket" in text

    # Concept label should appear (whitelisted)
    assert re.search(r'lunt_requests_total{.*concepto="MURO-BLOCK".*}', text) is not None
    # Confidence and alternatives metrics present
    assert "lunt_nl_resolve_confidence_score_bucket" in text
    assert "lunt_nl_resolve_alternatives_total" in text
