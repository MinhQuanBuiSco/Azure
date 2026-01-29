"""Multi-Model LLM Routing System.

A production-ready system that intelligently routes queries to cost-effective
model tiers based on complexity analysis, semantic classification, and budget constraints.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api import (
    analytics_router,
    budget_router,
    chat_router,
    health_router,
)
from backend.config import get_settings
from backend.storage import get_cosmos_client, get_redis_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan management."""
    settings = get_settings()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")

    # Initialize storage clients
    try:
        cosmos = get_cosmos_client(settings)
        await cosmos.initialize_containers()
        logger.info("Cosmos DB containers initialized")
    except Exception as e:
        logger.warning(f"Cosmos DB initialization skipped: {e}")

    try:
        redis = get_redis_client(settings)
        if await redis.health_check():
            logger.info("Redis connection established")
    except Exception as e:
        logger.warning(f"Redis connection skipped: {e}")

    yield

    # Cleanup
    logger.info("Shutting down...")
    try:
        redis = get_redis_client(settings)
        await redis.close()
    except Exception:
        pass

    try:
        cosmos = get_cosmos_client(settings)
        await cosmos.close()
    except Exception:
        pass


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Multi-Model LLM Routing System - Intelligent query routing "
            "to cost-effective model tiers based on complexity analysis, "
            "semantic classification, and budget constraints."
        ),
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(health_router)
    app.include_router(chat_router)
    app.include_router(analytics_router)
    app.include_router(budget_router)

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "detail": str(exc) if settings.debug else "An unexpected error occurred",
            },
        )

    return app


# Create the application instance
app = create_app()
