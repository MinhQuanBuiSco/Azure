import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .services import cache_service
from .models.schemas import HealthResponse
from .api.routes import upload, index, query, cache

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting up RAG Application...")
    try:
        # Connect to Redis
        await cache_service.connect()
        logger.info("Connected to Redis cache")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")

    yield

    # Shutdown
    logger.info("Shutting down RAG Application...")
    try:
        await cache_service.disconnect()
        logger.info("Disconnected from Redis")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="RAG Application with Entity Extraction and Multi-Strategy Search",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router, prefix="/api")
app.include_router(index.router, prefix="/api")
app.include_router(query.router, prefix="/api")
app.include_router(cache.router, prefix="/api")


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """
    Health check endpoint.

    Returns:
        Application health status
    """
    services = {}

    # Check Redis
    try:
        await cache_service.redis_client.ping()
        services["redis"] = "healthy"
    except Exception:
        services["redis"] = "unhealthy"

    # Check Azure services (basic check)
    try:
        from .services import BlobStorageService
        blob_service = BlobStorageService()
        services["blob_storage"] = "healthy"
    except Exception:
        services["blob_storage"] = "unhealthy"

    return HealthResponse(
        status="healthy" if all(v == "healthy" for v in services.values()) else "degraded",
        version=settings.app_version,
        services=services
    )


@app.get("/", tags=["root"])
async def root():
    """Root endpoint."""
    return {
        "message": "RAG Application API",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
