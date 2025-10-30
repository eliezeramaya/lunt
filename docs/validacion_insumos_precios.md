# Validación de Insumos y Precios (Paso 1.1)

Este módulo ejecuta una validación previa al cálculo para asegurar:

- Cada receta tiene al menos un insumo activo a la fecha.
- Cada insumo tiene precio vigente para la ubicación y fecha solicitadas.
- En modo tolerante (`allow_missing_prices=True`), no se detiene; agrega warnings y marca `precio_unitario: null`.

Zona horaria: America/Mexico_City. Fechas en ISO `YYYY-MM-DD`.

## Modelos (Pydantic)

- `ValidacionParametros` con: `fecha`, `ubicacion_codigo`, `receta_codigos`, `allow_missing_prices`, `locale`.
- `InsumoValidado`: `insumo_codigo`, `cantidad`, `unidad`, `precio_unitario|null`, `moneda|null`, `warnings`.
- `RecetaValidada`: `receta_codigo`, `insumos`, `warnings`.
- `ResultadoValidacion`: `ok`, `recetas`, `warnings`, `errors`.

## Servicio

Función: `validar_insumos_y_precios(params, db)` en `api/services/validacion_insumos_precios.py`.

Reglas:

- `RECETAS_VACIAS` si la lista está vacía.
- `UBICACION_INVALIDA` si `ubicacion_codigo` no existe en `locations`.
- `RECETA_SIN_INSUMOS` si no hay filas activas en `concept_recipes` a la fecha.
- `CANTIDAD_INVALIDA` si `quantity <= 0`.
- `PRECIO_FALTANTE` si no hay precio vigente en `insumo_prices` (usa `valid_from <= fecha` y `valid_until` nulo o `>= fecha`), seleccionando el más reciente con `ROW_NUMBER()`.
- `MONEDA_FALTANTE` si el precio carece de moneda.

Comportamiento:

- Estricto (default): `ok=false` si hay 1+ errores. `recetas=[]`, `warnings=[]`, `errors=[...]`.
- Tolerante: `ok=true`, `errors=[]`, warnings en insumo y receta; insumos faltantes con `precio_unitario: null`, `moneda: null`.

## Endpoint

`POST /v1/motor/validar`

- Body: `ValidacionParametros`
- Resp: `ResultadoValidacion`
- Header: `X-Correlation-Id` añadido para trazabilidad.

### Ejemplos

Solicitud (estricto por defecto):

```
{
  "fecha": "2025-09-01",
  "ubicacion_codigo": "CDMX",
  "receta_codigos": ["REC-001", "REC-002"]
}
```

Respuesta (error estricto):

```
{
  "ok": false,
  "recetas": [],
  "warnings": [],
  "errors": [
    "Falta precio para el insumo CEM-001 en CDMX al 2025-09-01",
    "La receta REC-002 no contiene insumos."
  ]
}
```

Solicitud (tolerante):

```
{
  "fecha": "2025-09-01",
  "ubicacion_codigo": "CDMX",
  "receta_codigos": ["REC-001"],
  "allow_missing_prices": true
}
```

Respuesta (tolerante con warnings):

```
{
  "ok": true,
  "recetas": [
    {
      "receta_codigo": "REC-001",
      "warnings": ["1 insumo(s) sin precio en REC-001"],
      "insumos": [
        {
          "insumo_codigo": "CEM-001",
          "cantidad": 1.0,
          "unidad": "t",
          "precio_unitario": null,
          "moneda": null,
          "warnings": ["Falta precio para el insumo CEM-001 en CDMX al 2025-09-01"]
        }
      ]
    }
  ],
  "warnings": ["1 insumo(s) sin precio en REC-001"],
  "errors": []
}
```

## Performance

- Evita N+1: carga recetas e insumos en un join por todos los códigos, y resuelve precios vigentes con una sola consulta usando `ROW_NUMBER()` particionada por `insumo_id`.
- Índices recomendados (migración `004`):
  - `insumo_prices(insumo_id, location_code, valid_from DESC)`
  - `concept_recipes(concept_id)`

## Logs y trazabilidad

- Estructura de issue interno: `ValidationIssue(code, severity, context, message)`.
- Niveles: WARNING (tolerante), ERROR (estricto).
- Cabecera de respuesta `X-Correlation-Id` con UUID.

