from __future__ import annotations

from decimal import Decimal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Cargador de configuración (.env) para parámetros de costos.

    Variables esperadas:
    - LUNT_DEFAULT_PORC_INDIRECTOS
    - LUNT_DEFAULT_PORC_UTILIDAD
    """

    default_porc_indirectos: Decimal = Decimal("0.10")
    default_porc_utilidad: Decimal = Decimal("0.10")

    # NL resolver (3.1)
    nl_resolver_backend: str = "qdrant"
    nl_qdrant_url: str = "http://localhost:6333"
    nl_qdrant_api_key: str | None = None
    nl_qdrant_collection: str = "concepts_v1"
    nl_embed_model: str = "torch-mini-emb-384"
    nl_embed_dim: int = 384
    nl_topk: int = 5
    nl_topk_alt: int = 5
    nl_score_threshold: float = 0.72
    nl_normalize_scores: bool = True
    nl_gpt_model: str = "gpt-4o-mini"
    nl_gpt_system_prompt_path: str = "./prompts/nl_resolver_system.md"
    nl_enable_cache: bool = True
    nl_cache_ttl_sec: int = 3600
    nl_lang_default: str = "es"

    class Config:
        env_prefix = "LUNT_DEFAULT_"
        fields = {
            "default_porc_indirectos": {"env": "PORC_INDIRECTOS"},
            "default_porc_utilidad": {"env": "PORC_UTILIDAD"},
            "nl_resolver_backend": {"env": "NL_RESOLVER_BACKEND"},
            "nl_qdrant_url": {"env": "NL_QDRANT_URL"},
            "nl_qdrant_api_key": {"env": "NL_QDRANT_API_KEY"},
            "nl_qdrant_collection": {"env": "NL_QDRANT_COLLECTION"},
            "nl_embed_model": {"env": "NL_EMBED_MODEL"},
            "nl_embed_dim": {"env": "NL_EMBED_DIM"},
            "nl_topk": {"env": "NL_TOPK"},
            "nl_topk_alt": {"env": "NL_TOPK_ALT"},
            "nl_score_threshold": {"env": "NL_SCORE_THRESHOLD"},
            "nl_normalize_scores": {"env": "NL_NORMALIZE_SCORES"},
            "nl_gpt_model": {"env": "NL_GPT_MODEL"},
            "nl_gpt_system_prompt_path": {"env": "NL_GPT_SYSTEM_PROMPT_PATH"},
            "nl_enable_cache": {"env": "NL_ENABLE_CACHE"},
            "nl_cache_ttl_sec": {"env": "NL_CACHE_TTL_SEC"},
            "nl_lang_default": {"env": "NL_LANG_DEFAULT"},
        }


settings = Settings()


def get_settings() -> Settings:
    """Return a fresh Settings instance (reads current env)."""
    return Settings()


def resolve_percent(value: Decimal | None, fallback: Decimal) -> Decimal:
    """Resuelve un porcentaje efectivo validando rango 0..1."""
    if value is None:
        return fallback
    if value < 0 or value > 1:
        raise ValueError("El porcentaje debe ser una fracción entre 0 y 1.")
    return value
