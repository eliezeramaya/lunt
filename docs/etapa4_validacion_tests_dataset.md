# ETAPA 4 – Validación, Tests y Dataset

## 4.1 Tests parametrizados

- Fixtures reutilizables para catálogo, recetas y precios.
- Parametrización por `selection_mode`, `allow_missing_prices`, variantes y porcentajes.
- Validación de forma del JSON (claves en `breakdown`, `porcentajes_usados`, `meta.resolution`).
- Edge cases cubiertos: recetas sin insumos, precios faltantes, monedas distintas, empate en `strategy=cheapest`, bajas confianzas.

Ejecución:
- `pytest -q --maxfail=1 --disable-warnings --cov=api --cov-report=xml`

## 4.2 Registro de previews

- Tabla `preview_log` (Alembic `006_preview_log.py`).
- Servicio `api/services/preview_log.py` con:
  - `create_from_preview(...)` para insertar registros a partir de previews con descripción.
  - `mark_user_feedback(...)` para registrar correcciones del usuario.
- Endpoint `POST /v1/analytics/preview_feedback` (opcional) para recolección de feedback.
- Exportador `python -m lunt.tools.index_concepts` para poblar Qdrant (ETL); dataset de previews puede exportarse con herramientas externas (CSV/Parquet) a partir de la tabla.

Privacidad:
- Truncado de `description` a 512 chars.
- No almacenar PII; `user_id` opcional/anonimizado.

Métricas:
- `lunt_preview_logs_total{backend}`
- `lunt_preview_feedback_total{changed}`
- `lunt_preview_log_duration_seconds_bucket`

