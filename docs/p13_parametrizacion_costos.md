# p1.3 – Parametrización de fórmulas de costos

Permite configurar porcentajes de indirectos y utilidad por parámetros o variables de entorno, con fórmula determinística y redondeos consistentes.

## Configuración (.env)

- `LUNT_DEFAULT_PORC_INDIRECTOS` (ej. `0.10`)
- `LUNT_DEFAULT_PORC_UTILIDAD` (ej. `0.10`)

Cargadas por `api/services/settings.py` (pydantic-settings). Precedencia: parámetro > env > fallback interno (`0.10`, `0.10`).

## DTOs

- `CostParams`: incluye `porcentaje_indirectos`, `porcentaje_utilidad`, `selection_mode` (p1.2), `allow_missing_prices`, `output_scale_decimals`.
- `CostBreakdown`: `costo_directo`, `indirectos_pct/monto`, `subtotal_cd_i`, `utilidad_pct/monto`, `costo_total`.

## Servicio

`compute_cost(params, db)` en `api/services/costs.py`:
1) Resuelve porcentajes efectivos.
2) Usa p1.2 (`get_recipes_for_concept`) para variantes e insumos, evitando N+1 y reusando precios vigentes.
3) Aplica fórmula con `Decimal` y `ROUND_HALF_UP`. Interno: 4 decimales, salida: `output_scale_decimals`.
4) Maneja faltantes de precio (COSTO_PARCIAL) y monedas múltiples (MONEDA_INCONSISTENTE, omite moneda distinta a mayoritaria).

## Fórmula

- `costo_directo = Σ(cantidad * precio_unitario)`
- `indirectos_monto = costo_directo * porcentaje_indirectos`
- `subtotal_cd_i = costo_directo + indirectos_monto`
- `utilidad_monto = subtotal_cd_i * porcentaje_utilidad`
- `costo_total = subtotal_cd_i + utilidad_monto`

## Endpoint

`POST /v1/motor/costos/preview`

Response incluye `porcentajes_usados` y `breakdown`, además de `meta.percent_source` y `meta.rounding`.

## Ejemplos

A) Sin parámetros (usa .env)

```
{
  "porcentajes_usados": {"indirectos": 0.10, "utilidad": 0.10},
  "breakdown": {"costo_total": 1839.51}
}
```

B) Con parámetros

```
{
  "porcentajes_usados": {"indirectos": 0.08, "utilidad": 0.12},
  "breakdown": {"costo_total": 1838.89}
}
```

## Pruebas

- Precedencia de parámetros/env
- Rango válido 0..1
- Integración con p1.1/p1.2 (estricto/tolerante, aggregate/single/strategy)
- Redondeo y determinismo de los cálculos

