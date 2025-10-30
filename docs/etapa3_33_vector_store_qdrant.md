# ETAPA 3 – Paso 3.3: Integración con vector store (Qdrant)

Arquitectura: embedding local → Qdrant → top‑k candidatos → resolver → meta.resolution (confidence_score + alternatives).

## Configuración (.env)

- `NL_RESOLVER_BACKEND=qdrant`
- `NL_QDRANT_URL=http://qdrant:6333`
- `NL_QDRANT_API_KEY=`
- `NL_QDRANT_COLLECTION=concepts_v1`
- `NL_EMBED_MODEL=torch-mini-emb-384`
- `NL_EMBED_DIM=384`
- `NL_TOPK=5`
- `NL_TOPK_ALT=5`
- `NL_SCORE_THRESHOLD=0.72`
- `NL_NORMALIZE_SCORES=true`
- `NL_ENABLE_CACHE=true`
- `NL_CACHE_TTL_SEC=3600`
- `NL_LANG_DEFAULT=es`

## Componentes

- `EmbeddingModel` y `LocalSentenceEncoder`: embeddings deterministas sin red.
- `QdrantClientWrapper`: ensure_collection, upsert_points, search.
- `VectorSearcher`: normaliza texto, usa caché (Redis opcional), llama a Qdrant, normaliza scores a [0..1] y retorna `[(concept_code, score)]`.
- `QdrantResolver`: delega 100% en `VectorSearcher` y llena `ConceptResolution`.

## Métricas

- `lunt_nl_vector_requests_total{backend,ok}`
- `lunt_nl_vector_duration_seconds_bucket{backend}`
- `lunt_nl_vector_confidence_score_bucket{backend}`
- `lunt_nl_vector_topk_returned_total{backend}`

## ETL

Script `python -m lunt.tools.index_concepts`:
- Lee conceptos de DB.
- Construye `text_canonical` con nombre/aliases/tags.
- Genera embeddings locales.
- Upsert a Qdrant con payload completo `{concept_code, concept_name, aliases, tags, lang}`.

## Operación

- Distancia recomendada: Cosine.
- Control de cardinalidad: no etiquetar métricas con concept_code salvo whitelist.
- Backups/rotación: usar alias `concepts_v1 → concepts_v2` para despliegues sin downtime.

