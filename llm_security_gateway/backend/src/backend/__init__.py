"""LLM Security Gateway - FastAPI Application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import audit, chat, completions, health
from backend.api.middleware.logging import RequestLoggingMiddleware
from backend.config.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    settings = get_settings()
    print(f"Starting LLM Security Gateway v0.1.0")
    print(f"Environment: {settings.environment}")

    # Preload security scanner (including Presidio/spaCy) to avoid slow first request
    print("Preloading security scanner...")
    try:
        from backend.security.scanner import get_security_scanner
        scanner = get_security_scanner()
        # Warm up with a test scan
        await scanner.scan("warmup test")
        print("Security scanner preloaded successfully")
    except Exception as e:
        print(f"Warning: Failed to preload security scanner: {e}")

    yield
    print("Shutting down LLM Security Gateway")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="LLM Security Gateway",
        description="A security layer for LLM applications providing prompt injection detection, PII masking, rate limiting, and audit logging.",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS middleware
    # Note: allow_credentials must be False when using allow_origins=["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request logging middleware
    app.add_middleware(RequestLoggingMiddleware)

    # Include routers
    app.include_router(health.router, tags=["Health"])
    app.include_router(chat.router, prefix="/v1", tags=["Chat"])
    app.include_router(completions.router, prefix="/v1", tags=["Completions"])
    app.include_router(audit.router, prefix="/api", tags=["Audit"])

    return app


app = create_app()
