from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.services.db import get_db
from api.services.preview_log import mark_user_feedback


router = APIRouter(prefix="/v1/analytics", tags=["analytics"])


class PreviewFeedback(BaseModel):
    log_id: str = Field(..., description="ID del registro de preview")
    final_concept_code: str = Field(..., description="Código de concepto confirmado/corregido")
    was_correct: bool | None = Field(None, description="Si la inferencia original fue correcta")
    notes: str | None = Field(None, description="Notas opcionales")


@router.post("/preview_feedback")
async def preview_feedback(payload: PreviewFeedback, db: AsyncSession = Depends(get_db)):
    try:
        await mark_user_feedback(
            db,
            log_id=payload.log_id,
            final_concept_code=payload.final_concept_code,
            was_correct=payload.was_correct,
            notes=payload.notes,
        )
        return {"ok": True}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=500, detail="Error al registrar feedback") from e

