# ETAPA 2 – Paso 2.2: Logging detallado de breakdown

Implementa logging estructurado (JSON por línea) para trazabilidad completa del motor de costos.

## Eventos

- pricing.start (INFO): contexto de cálculo (concepto, ubicación, fecha, selección, strategy, porcentajes).
- pricing.variants (INFO/DEBUG): variantes evaluadas y la usada.
- pricing.prices (DEBUG/INFO): lote de insumos con cantidades, precio unitario y moneda.
- pricing.breakdown_step (DEBUG): pasos de cálculo con acumuladores.
- pricing.warning (WARNING): avisos (faltantes, moneda).
- pricing.error (ERROR): errores fatales en estricto.
- pricing.breakdown_final (INFO): desglose final con porcentajes.
- pricing.end (INFO): tiempos por sección y total.

## Campos base

Todos los eventos incluyen: `evt`, `level`, `correlation_id`, `service`, `env`, `version`, `ts` (zona America/Mexico_City).

## Sampling DEBUG

`LUNT_LOG_DEBUG_SAMPLING` ∈ [0,1]. Si <1, se emiten eventos DEBUG solo para una fracción de requests basada en hash de `correlation_id`.

## Integración

- Middleware agrega/propaga `X-Correlation-Id` y lo expone en `request.state.correlation_id`.
- `api/services/costs.compute_cost` emite `start`, `variants`, `prices`, `breakdown_final`, `end` y mide secciones.
- `api/services/pricing_strategies.DefaultPricingStrategy` emite `prices` (detalle), `breakdown_step`, `warning/error` según reglas.

## Observabilidad

Ejemplos de líneas se pueden capturar y enviar a ELK/Datadog. Evita PII. Niveles por severidad.

