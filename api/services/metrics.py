from __future__ import annotations

import os
import time
from typing import Callable

from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.requests import Request


# Buckets for HTTP request latency (seconds)
HTTP_LATENCY_BUCKETS = (
    0.025,
    0.05,
    0.1,
    0.25,
    0.5,
    1.0,
    2.5,
    5.0,
    7.5,
    10.0,
)

# Env configuration
METRICS_ENABLED = os.getenv("LUNT_METRICS_ENABLED", "true").lower() == "true"
METRICS_PATH = os.getenv("LUNT_METRICS_PATH", "/metrics")
WHITELIST: set[str] = set(filter(None, os.getenv("LUNT_METRICS_CONCEPTS_WHITELIST", "").split(",")))


def normalize_concept(value: str | None) -> str:
    if not value:
        return "__unknown__"
    if not WHITELIST:
        return value
    return value if value in WHITELIST else "__other__"


# Request-level metrics with endpoint + method + status + concepto
REQ_COUNTER = Counter(
    "lunt_requests_total",
    "Total de requests a endpoints del motor",
    labelnames=("endpoint", "method", "status", "concepto"),
)

REQ_LATENCY = Histogram(
    "lunt_request_latency_seconds",
    "Latencia de request por endpoint",
    labelnames=("endpoint", "method", "status", "concepto"),
    buckets=HTTP_LATENCY_BUCKETS,
)


def _endpoint_from_request(req: Request) -> str:
    try:
        route = req.scope.get("route")
        return getattr(route, "path", "__unknown__")
    except Exception:
        return "__unknown__"


def custom_metrics() -> Callable:
    def instrumentation(info) -> None:
        # 'info' is an instance from the instrumentator with request/response/duration
        req = info.request
        res = info.response
        endpoint = _endpoint_from_request(req)
        method = req.method
        status = str(res.status_code)
        concepto = getattr(req.state, "concepto", "__unknown__")
        REQ_COUNTER.labels(endpoint, method, status, concepto).inc()
        REQ_LATENCY.labels(endpoint, method, status, concepto).observe(info.duration)

    return instrumentation


# Engine metrics (strategy compute)
ENGINE_LATENCY = Histogram(
    "lunt_engine_compute_seconds",
    "Duración del cálculo del motor (PricingEngine.compute)",
    labelnames=("selection_mode", "strategy"),
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5),
)

ENGINE_COUNTER = Counter(
    "lunt_engine_requests_total",
    "Total de ejecuciones del motor",
    labelnames=("selection_mode", "strategy"),
)


def record_engine_metrics(selection_mode: str, strategy: str, elapsed_seconds: float) -> None:
    ENGINE_COUNTER.labels(selection_mode, strategy).inc()
    ENGINE_LATENCY.labels(selection_mode, strategy).observe(elapsed_seconds)


# NL resolver metrics
NL_REQ = Counter(
    "lunt_nl_resolve_requests_total",
    "Total de resoluciones NL a concepto",
    labelnames=("backend", "ok", "resolved_concept"),
)

NL_LAT = Histogram(
    "lunt_nl_resolve_duration_seconds",
    "Duración de la resolución NL",
    labelnames=("backend",),
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5),
)

NL_LOWCONF = Counter(
    "lunt_nl_resolve_low_confidence_total",
    "Resoluciones NL con baja confianza (< threshold)",
    labelnames=("backend",),
)


def record_nl_metrics(backend: str, ok: bool, elapsed_seconds: float, *, resolved_concept: str | None) -> None:
    concept_label = normalize_concept(resolved_concept)
    NL_REQ.labels(backend, str(ok).lower(), concept_label).inc()
    NL_LAT.labels(backend).observe(elapsed_seconds)

def record_nl_low_confidence(backend: str) -> None:
    NL_LOWCONF.labels(backend).inc()

# Confidence distribution and alternatives count
NL_CONF_HISTO = Histogram(
    "lunt_nl_resolve_confidence_score",
    "Distribución de score de confianza en ConceptResolver",
    labelnames=("backend",),
    buckets=(0.0, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
)

NL_ALT_COUNT = Counter(
    "lunt_nl_resolve_alternatives_total",
    "Cantidad de sugerencias alternativas generadas",
    labelnames=("backend",),
)


def record_nl_confidence(backend: str, score: float | None, alt_count: int) -> None:
    NL_CONF_HISTO.labels(backend).observe(float(score or 0.0))
    NL_ALT_COUNT.labels(backend).inc(alt_count)

# Vector search metrics
NL_VECTOR_REQ = Counter(
    "lunt_nl_vector_requests_total",
    "Total de búsquedas vectoriales",
    labelnames=("backend", "ok"),
)

NL_VECTOR_LAT = Histogram(
    "lunt_nl_vector_duration_seconds",
    "Duración de búsquedas vectoriales",
    labelnames=("backend",),
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5),
)

NL_VECTOR_CONF = Histogram(
    "lunt_nl_vector_confidence_score",
    "Distribución de score top-1 en búsquedas vectoriales",
    labelnames=("backend",),
    buckets=(0.0, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
)

NL_VECTOR_TOPK = Counter(
    "lunt_nl_vector_topk_returned_total",
    "Cantidad de candidatos devueltos por búsqueda",
    labelnames=("backend",),
)


def record_nl_vector_metrics(*, ok: bool, elapsed_seconds: float) -> None:
    NL_VECTOR_REQ.labels("qdrant", str(ok).lower()).inc()
    NL_VECTOR_LAT.labels("qdrant").observe(elapsed_seconds)


def record_nl_vector_confidence(score: float | None) -> None:
    NL_VECTOR_CONF.labels("qdrant").observe(float(score or 0.0))


def record_nl_vector_topk(n: int) -> None:
    NL_VECTOR_TOPK.labels("qdrant").inc(n)

# Preview logging metrics
PREVIEW_LOG_COUNTER = Counter(
    "lunt_preview_logs_total",
    "Total de registros de preview",
    labelnames=("backend",),
)

PREVIEW_FEEDBACK_COUNTER = Counter(
    "lunt_preview_feedback_total",
    "Total de feedback de preview",
    labelnames=("changed",),
)

PREVIEW_LOG_LAT = Histogram(
    "lunt_preview_log_duration_seconds",
    "Duración del registro de preview",
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5),
)


def record_preview_log_created(*, backend: str) -> None:
    PREVIEW_LOG_COUNTER.labels(backend).inc()


def record_preview_feedback(*, changed: bool) -> None:
    PREVIEW_FEEDBACK_COUNTER.labels("true" if changed else "false").inc()


def instrument_app(app) -> None:
    if not METRICS_ENABLED:
        return
    instrumentator = Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        should_respect_env_var=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=[METRICS_PATH],
    )
    instrumentator.add(custom_metrics()).instrument(app).expose(
        app, endpoint=METRICS_PATH, include_in_schema=False
    )
