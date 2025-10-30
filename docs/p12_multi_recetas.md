# p1.2 – Soporte para múltiples recetas por concepto

Extiende el motor para manejar múltiples variantes de receta por concepto. Mantiene compatibilidad (modo aggregate) y habilita selección explícita o estratégica.

## Modelado

Tabla `concept_recipes` ampliada:
- `variant_id` (string, not null)
- `variant_label` (string)
- `recipe_code` (string)
- `active` (bool, default true)
- índices: `(concept_id, variant_id)`, `(concept_id, active)`

## API

Endpoint: `POST /v1/motor/recetas/preview`

Request (RecipeRequestParams):
- `concepto_codigo`, `fecha`, `ubicacion_codigo`
- `selection_mode`: `aggregate` | `single` | `strategy`
- `recipe_variant_id` (si `single`)
- `strategy`: `cheapest` | `latest` | `strongest` (placeholder)
- `allow_missing_prices`

Response (RecipePreview):
- `selection_mode`, `used_variant_id`, `used_strategy`
- `variants_considered[]` con `aggregated_cost`
- `insumos[]` con `source_variant_id`
- `warnings[]`, `errors[]`

## Selección

- aggregate (default): suma cantidades por `(insumo_codigo, unidad)`, `source_variant_id="multiple"`.
- single: requiere `recipe_variant_id` válido.
- strategy:
  - cheapest: minimiza tuple `(faltantes, costo)`; empate -> receta_codigo asc (warning `EMPATE_ESTRATEGIA`).
  - latest: usa `receta_id` más reciente (proxy a falta de metadata).
  - strongest: placeholder, prioriza `variant_label` que contenga "reforz".

## Precios y validación

- Integra precios con p1.1 (`get_precios_vigentes`) en un solo roundtrip para todas las variantes.
- Estricto (`allow_missing_prices=false`): si falta precio en variante(s) seleccionadas, retorna `errors[]`.
- Tolerante: `precio_unitario=null`, warnings por insumo y resumen de variante.

## Ejemplo (aggregate)

```
{
  "concepto_codigo": "MURO-BLOCK",
  "selection_mode": "aggregate",
  "variants_considered": [
    {"variant_id":"std","variant_label":"estandar","receta_codigo":"REC-MB-STD","aggregated_cost": 1520.25},
    {"variant_id":"ref","variant_label":"reforzada","receta_codigo":"REC-MB-REF","aggregated_cost": 1987.40}
  ],
  "insumos": [
    {"insumo_codigo":"CEM-001","cantidad":1.2,"unidad":"t","precio_unitario":null,"moneda":null,"source_variant_id":"multiple"}
  ]
}
```

## Migración

`005_multi_recipe_variants.py` agrega columnas e índices.

## Compatibilidad

El modo `aggregate` replica el comportamiento previo (suma de todas las filas vigentes en `concept_recipes`).

