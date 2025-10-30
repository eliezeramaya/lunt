# ETAPA 2 – Paso 2.1: Strategy Pattern para el motor de costos

## Motivación
Desacoplar la fórmula de costos del flujo de preparación de datos (p1.1/p1.2/p1.3) para permitir múltiples estrategias (por defecto, específicas por cliente o IA) con observabilidad y trazabilidad.

## Diseño

```
PricingEngine
  ├─ BasePricingStrategy (Protocol)
  │     └─ calcular_precio(ctx: PricingContext) -> PricingResult
  ├─ DefaultPricingStrategy (impl)
  └─ [futuras: CheapestStrategy, MLStrategy, ...]
  (usa) PricingContext -> PricingResult
```

- `PricingContext`: entrada con insumos (ya validados y con precios resueltos), porcentajes, flags y meta (variants, strategy, percent_source, correlation_id).
- `PricingResult`: `PricingBreakdown` + `meta` (incluye `strategy` y `rounding`).
- `DefaultPricingStrategy`: implementa la fórmula actual 1:1 (costo directo + indirectos + utilidad), mantiene resultados previos.
- `PricingEngine`: recibe la estrategia (o usa default) y ejecuta `compute` con logs estructurados.
- Registry: `get_pricing_strategy(name)` permite inyección por string.

## Monedas y faltantes
- Por compatibilidad con p1.3, la estrategia por defecto tolera monedas múltiples con warning y omite insumos en moneda distinta a la mayoritaria (si no hay módulo FX).
- Faltantes de precio: en estricto aborta; en tolerante suma costo parcial con warning `COSTO_PARCIAL`.

## Uso
- Endpoint: `POST /v1/motor/costos/preview` ahora acepta `pricing_strategy` (string). Si se omite, usa `default`.
- `api/services/costs.py` construye `PricingContext` tras p1.1/p1.2/p1.3 y delega a `PricingEngine`.

## Observabilidad
- Logs incluyen: `strategy`, `fecha`, `ubicacion`, `costo_directo`, `indirectos_monto`, `utilidad_monto`, `costo_total`, conteo de warnings/errors.

## Extender
- Registrar nuevas estrategias en `PRICING_STRATEGIES` del módulo `api/services/pricing_strategies.py`.
- Implementar clase con `name` y método `calcular_precio(ctx)`.

## Compatibilidad
- DefaultPricingStrategy reproduce exactamente los números previos. No hay migraciones de DB.

