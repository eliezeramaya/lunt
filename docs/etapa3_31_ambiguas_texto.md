# ETAPA 3 – Paso 3.1: Soporte a descripciones ambiguas (NL → Concepto)

Permite invocar el motor con `description` si `concepto_codigo` no está presente. Integra con p1.1, p1.2, p1.3, Strategy 2.1, Logging 2.2 y métricas.

## Flujo

1) Entrada `CostParams` extendida con `description` y `language`.
2) Si falta `concepto_codigo` y hay `description`, se invoca `ConceptResolver`.
3) Si score ≥ threshold → usar `concepto_codigo` resuelto; si no, devolver error con candidatos.
4) Continuar pipeline (p1.2 → p1.1 → p1.3 → Strategy) y responder con `meta.resolution`.

## Configuración

```
NL_RESOLVER_BACKEND=qdrant|gpt
NL_QDRANT_URL=http://qdrant:6333
NL_QDRANT_API_KEY=
NL_QDRANT_COLLECTION=concepts_v1
NL_EMBED_MODEL=text-embedding-3-small
NL_TOPK=5
NL_SCORE_THRESHOLD=0.72
NL_GPT_MODEL=gpt-4o-mini
NL_GPT_SYSTEM_PROMPT_PATH=./prompts/nl_resolver_system.md
NL_ENABLE_CACHE=true
```

## Interfaces

- `api/schemas/nl.ConceptResolution`: {ok, concept_code, score, candidates, guidance, backend}
- `api/services/concept_resolver.IConceptResolver.resolve(description, language, topk)`

Backend actual: `SimpleResolver` (placeholder) con búsqueda LIKE (listo para reemplazar por Qdrant/GPT).

## Logging (2.2)

- `nl.resolve.start` (INFO)
- `nl.resolve.result` (INFO)
- `nl.resolve.warn_low_score` (WARNING)

## Métricas

- `lunt_nl_resolve_requests_total{backend,ok,resolved_concept}` (con whitelist de concepto)
- `lunt_nl_resolve_duration_seconds_bucket{backend}`
- `lunt_nl_resolve_low_confidence_total{backend}`

## Errores

- Falta de ambos campos: error con mensaje claro.
- Baja confianza: error con candidatos y guidance en `meta.resolution`.
- Concepto inexistente: 404 (a manejar si el catálogo no contiene el código resuelto).

