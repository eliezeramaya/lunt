import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import confirm, preview, recalc, series
from api.services.cache import close_redis, get_redis
from api.services.db import close_db

API_TITLE = os.getenv("API_TITLE", "Lunt API")
API_DESCRIPTION = os.getenv(
    "API_DESCRIPTION", "Sistema inteligente de analisis y gestion de costos de construccion"
)
API_VERSION = os.getenv("API_VERSION", "v1")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle events for FastAPI application
    Startup: Initialize Redis connection
    Shutdown: Close Redis and DB connections
    """
    await get_redis()
    print("Redis connection established")
    yield
    await close_redis()
    await close_db()
    print("Connections closed")


app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(preview.router)
app.include_router(recalc.router)
app.include_router(confirm.router)
app.include_router(series.router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Lunt API",
        "version": API_VERSION,
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Lunt API - Sistema de gestion de costos de construccion",
        "docs": "/docs",
        "health": "/health",
        "version": API_VERSION,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=os.getenv("DEBUG", "false").lower() == "true",
    )
