# ETAPA 3 – Paso 3.2: Feedback de confianza (score y alternativas)

Añade transparencia en la resolución NL→Concepto incluyendo `confidence_score` y `alternatives` en `meta.resolution` del preview.

## Campos

- `confidence_score` (0..1): nivel de confianza del resolver.
- `alternatives`: lista de conceptos candidatos con `score` (top-N, configurable con `NL_TOPK_ALT`).
- `guidance`: texto explicativo breve.

## Ejemplo

```
"meta": {
  "resolution": {
    "backend": "qdrant",
    "concept_code": "MURO-BLOCK-REF",
    "confidence_score": 0.87,
    "alternatives": [
      {"concept_code": "MURO-BLOCK-STD", "score": 0.79},
      {"concept_code": "MURO-ACUSTICO", "score": 0.65}
    ],
    "guidance": "Se seleccionó 'REF' por palabras clave"
  }
}
```

## Logging y métricas

- Eventos: `nl.resolve.confidence` (INFO) y `nl.resolve.low_confidence` (WARNING).
- Métricas:
  - `lunt_nl_resolve_confidence_score_bucket{backend}`
  - `lunt_nl_resolve_alternatives_total{backend}`

## Umbral

Ajusta `NL_SCORE_THRESHOLD` para marcar baja confianza (422 en estricto) y orientar correcciones.

