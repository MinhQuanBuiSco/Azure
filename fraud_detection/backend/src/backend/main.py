"""
FastAPI application entry point for Fraud Detection System.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.v1 import transactions, alerts, rules, analytics, websocket
from backend.core.config import get_settings
from backend.services.cache import init_cache, close_cache


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    settings = get_settings()
    print(f"🚀 Starting {settings.app_name} v{settings.app_version}")

    # Initialize Redis cache
    try:
        await init_cache()
    except Exception as e:
        print(f"⚠️  Warning: Could not connect to Redis: {e}")
        print("   Continuing without cache...")

    yield

    # Shutdown
    print("👋 Shutting down Fraud Detection API")
    await close_cache()


# Initialize FastAPI app
app = FastAPI(
    title="Fraud Detection API",
    description="Enterprise-grade fraud detection system with real-time scoring",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(transactions.router, prefix="/api/v1", tags=["transactions"])
app.include_router(alerts.router, prefix="/api/v1", tags=["alerts"])
app.include_router(rules.router, prefix="/api/v1", tags=["rules"])
app.include_router(analytics.router, prefix="/api/v1", tags=["analytics"])
app.include_router(websocket.router, prefix="/api/v1", tags=["websocket"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    from backend.services.cache import get_cache

    cache = get_cache()
    cache_status = "healthy" if await cache.ping() else "unhealthy"

    return {
        "status": "healthy",
        "service": "fraud-detection-api",
        "version": "0.1.0",
        "cache": cache_status
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Fraud Detection API",
        "docs": "/docs",
        "health": "/health"
    }


def main():
    """Run the application."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
