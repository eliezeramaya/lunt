"""
Lunt API - Sistema inteligente de análisis y gestión de costos de construcción.

Features:
- CORS restrictivo por entorno
- Rate limiting por IP
- Métricas Prometheus en /metrics
- Logs estructurados en JSON
- Health check sin rate limit
"""

import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from api.routers import confirm, preview, recalc, series
from api.services.cache import close_redis, get_redis
from api.services.db import close_db
from api.services.logging_config import configure_logging, get_logger

# Environment configuration
API_TITLE = os.getenv("API_TITLE", "Lunt API")
API_DESCRIPTION = os.getenv(
    "API_DESCRIPTION",
    "Sistema inteligente de analisis y gestion de costos de construccion",
)
API_VERSION = os.getenv("API_VERSION", "v1")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# CORS configuration
# NOTE: In production, set ALLOWED_ORIGINS to exact domains only
ALLOWED_ORIGINS_STR = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://localhost:8000",
)
ALLOWED_ORIGINS = [origin.strip() for origin in ALLOWED_ORIGINS_STR.split(",")]

# Rate limiting configuration
# NOTE: Adjust RATE_LIMIT_DEFAULT based on expected traffic
RATE_LIMIT_DEFAULT = os.getenv("RATE_LIMIT_DEFAULT", "100/minute")
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"

# Logging configuration
# NOTE: Set JSON_LOGS=false in development for human-readable logs
JSON_LOGS = os.getenv("JSON_LOGS", "true").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Configure structured logging
configure_logging(level=LOG_LEVEL, json_logs=JSON_LOGS)
logger = get_logger(__name__)


# Rate limiter instance
# NOTE: Uses in-memory storage by default. For production with multiple workers,
# consider using Redis: limiter = Limiter(key_func=get_remote_address, storage_uri="redis://localhost:6379")
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle events for FastAPI application.

    Startup:
    - Initialize Redis connection
    - Log configuration

    Shutdown:
    - Close Redis and DB connections
    """
    await get_redis()
    logger.info(
        "Application startup complete",
        extra={
            "environment": ENVIRONMENT,
            "debug": DEBUG,
            "allowed_origins": ALLOWED_ORIGINS,
            "rate_limit_enabled": RATE_LIMIT_ENABLED,
        },
    )
    yield
    await close_redis()
    await close_db()
    logger.info("Application shutdown complete")


app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware
# NOTE: In production, ALLOWED_ORIGINS should contain only trusted domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Rate limiter state
if RATE_LIMIT_ENABLED:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    logger.info("Rate limiting enabled", extra={"default_limit": RATE_LIMIT_DEFAULT})


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log all HTTP requests with latency and status code.

    NOTE: Logs are structured JSON in production for easy parsing by log aggregators.
    """
    start_time = time.time()

    # Skip logging for health and metrics endpoints to reduce noise
    if request.url.path in ["/health", "/metrics"]:
        return await call_next(request)

    response = await call_next(request)
    latency_ms = (time.time() - start_time) * 1000

    logger.info(
        "HTTP request processed",
        extra={
            "http_method": request.method,
            "http_path": request.url.path,
            "status_code": response.status_code,
            "latency_ms": round(latency_ms, 2),
            "client_ip": get_remote_address(request),
        },
    )

    return response


# Prometheus metrics instrumentation
# NOTE: Exposes /metrics endpoint with p50/p95/p99 latencies per endpoint
instrumentator = Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/health", "/metrics"],
    env_var_name="ENABLE_METRICS",
    inprogress_name="http_requests_inprogress",
    inprogress_labels=True,
)

instrumentator.instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
logger.info("Prometheus metrics enabled at /metrics")


# Include routers
app.include_router(preview.router)
app.include_router(recalc.router)
app.include_router(confirm.router)
app.include_router(series.router)


@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    NOTE: This endpoint is NOT rate-limited and excluded from metrics
    to allow health checkers to poll freely.
    """
    return {
        "status": "healthy",
        "service": "Lunt API",
        "version": API_VERSION,
        "environment": ENVIRONMENT,
    }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Lunt API - Sistema de gestion de costos de construccion",
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics",
        "version": API_VERSION,
        "environment": ENVIRONMENT,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=DEBUG,
        log_config=None,  # Use our custom logging configuration
    )
