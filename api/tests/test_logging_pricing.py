from __future__ import annotations

import json
from datetime import date
from decimal import Decimal

import logging
import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.models import Concept, ConceptRecipe, Insumo, InsumoPrice
from api.models.users_locations import Location


def _parse_log_records(caplog):
    lines = []
    for rec in caplog.records:
        try:
            lines.append(json.loads(rec.getMessage()))
        except Exception:
            continue
    return lines


@pytest.mark.asyncio
async def test_logging_events_info_and_debug_sampling(db_session, caplog, monkeypatch):
    # Enable DEBUG and full sampling for this test
    monkeypatch.setenv("LUNT_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("LUNT_LOG_DEBUG_SAMPLING", "1.0")

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

    caplog.set_level(logging.DEBUG)
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

    lines = _parse_log_records(caplog)
    # Ensure required events exist
    evts = {l.get("evt") for l in lines}
    assert "pricing.start" in evts
    assert "pricing.variants" in evts
    assert "pricing.breakdown_final" in evts
    assert "pricing.end" in evts

    # Check DEBUG prices or breakdown_step present due to sampling=1.0
    assert any(l.get("evt") in {"pricing.prices", "pricing.breakdown_step"} for l in lines)

    # All events include correlation_id
    assert all("correlation_id" in l and l["correlation_id"] for l in lines if l.get("evt", "").startswith("pricing."))

