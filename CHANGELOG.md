# Changelog

- Paso 1.1 – Validación exhaustiva de insumos y precios
  - Nuevo servicio `validar_insumos_y_precios` con modo estricto/tolerante.
  - Endpoint `POST /v1/motor/validar` que retorna `ResultadoValidacion`.
  - Queries optimizadas: join de recetas/insumos y window function para precios vigentes.
  - Migración `004` con índices de soporte.
  - Tests unitarios, property-based (Hypothesis) y E2E del endpoint.
  - Documentación en `docs/validacion_insumos_precios.md`.

- p1.2 – Soporte para múltiples recetas por concepto
  - Nuevas columnas de variantes en `concept_recipes` con migración `005`.
  - Servicio `get_recipes_for_concept` con modos `aggregate`, `single` y `strategy` (cheapest/latest/strongest placeholder).
  - Endpoint `POST /v1/motor/recetas/preview` con trazabilidad de variantes.
  - Integración con p1.1 para resolución de precios y warnings/errores.
  - Tests unitarios y E2E.
  - Documentación en `docs/p12_multi_recetas.md`.

- p1.3 – Parametrización de fórmulas de costos
  - Nuevos DTOs `CostParams` y `CostBreakdown`.
  - Servicio `compute_cost` con porcentajes configurables por parámetros o .env.
  - Endpoint `POST /v1/motor/costos/preview` que expone `porcentajes_usados` y `breakdown`.
  - Módulo de configuración `api/services/settings.py` con pydantic-settings.
  - Warnings/errores claros, redondeo HALF_UP y trazabilidad.
  - Tests unitarios y E2E.
  - Documentación en `docs/p13_parametrizacion_costos.md`.

- ETAPA 2 – Paso 2.1: Strategy Pattern en motor de costos
  - Clases `BasePricingStrategy`, `DefaultPricingStrategy`, `PricingEngine` y registro de estrategias en `api/services/pricing_strategies.py`.
  - `compute_cost` delega a la estrategia seleccionada (parámetro `pricing_strategy`).
  - Logs estructurados de resultados.
  - Tests unitarios de estrategia y registry.
  - Documentación en `docs/etapa2_21_strategy.md`.

- ETAPA 2 – Paso 2.2: Logging detallado de breakdown
  - Módulo `lunt/logging.py` con `LogEvt`, `log_event`, `timed_section` y sampling DEBUG.
  - Middleware de `X-Correlation-Id` y propagación en `api/main.py`.
  - Logs en `compute_cost` y `DefaultPricingStrategy` (start, variants, prices, breakdown_step, breakdown_final, end).
  - Pruebas de logging con `caplog` (`api/tests/test_logging_pricing.py`).
  - Documentación en `docs/etapa2_22_logging_breakdown.md`.

- ETAPA 3 – Paso 3.1: Soporte a descripciones ambiguas (NL → Concepto)
  - Extensión de `CostParams` con `description` y `language`.
  - Resolver configurable `api/services/concept_resolver.py` con `ConceptResolution`.
  - Integración en `compute_cost` con logs y métricas de resolución.
  - Métricas: `lunt_nl_resolve_*` (requests, duration, low_confidence).
  - Documentación en `docs/etapa3_31_ambiguas_texto.md`.
  - Pruebas unitarias y E2E en `api/tests/test_nl_resolver.py`.

- ETAPA 3 – Paso 3.2: Feedback de confianza (score y alternativas)
  - `meta.resolution` ahora incluye `confidence_score` y `alternatives`.
  - Eventos de logging: `nl.resolve.confidence` y `nl.resolve.low_confidence`.
  - Métricas: `lunt_nl_resolve_confidence_score` (histograma) y `lunt_nl_resolve_alternatives_total`.
  - Documentación en `docs/etapa3_32_feedback_confianza.md`.

- ETAPA 3 – Paso 3.3: Integración con vector store (Qdrant)
  - `EmbeddingModel` local y `VectorSearcher` con `QdrantClientWrapper`.
  - `QdrantResolver` delega a `VectorSearcher` y completa `meta.resolution`.
  - Métricas: `lunt_nl_vector_*` (requests, duration, confidence, topk).
  - Script ETL `python -m lunt.tools.index_concepts` para poblar/actualizar la colección.
  - Documentación en `docs/etapa3_33_vector_store_qdrant.md`.

- ETAPA 4 – Validación, Tests y Dataset
  - 4.1: Tests parametrizados de engine y variaciones (api/tests/test_engine_variations.py).
  - 4.2: Tabla `preview_log`, servicio de logging (`api/services/preview_log.py`) y endpoint `POST /v1/analytics/preview_feedback`.
  - Métricas de analytics: `lunt_preview_logs_total`, `lunt_preview_feedback_total`, `lunt_preview_log_duration_seconds_bucket`.
  - Documentación en `docs/etapa4_validacion_tests_dataset.md`.
