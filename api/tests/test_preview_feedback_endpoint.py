from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.models.preview_log import PreviewLog


@pytest.mark.asyncio
async def test_preview_feedback_endpoint(db_session):
    # Create a preview_log row
    row = PreviewLog(description="desc", language="es")
    db_session.add(row)
    await db_session.flush()

    from api.services import db as db_module

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[db_module.get_db] = _override_get_db
    client = TestClient(app)
    resp = client.post(
        "/v1/analytics/preview_feedback",
        json={
            "log_id": row.id,
            "final_concept_code": "MURO-BLOCK",
            "was_correct": True,
        },
    )
    assert resp.status_code == 200
    await db_session.refresh(row)
    assert row.final_concept_code == "MURO-BLOCK"
    assert row.was_correct is True

