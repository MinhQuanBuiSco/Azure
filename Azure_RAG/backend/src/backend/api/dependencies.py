"""
FastAPI dependencies for lazy service initialization.
"""

from openai import AzureOpenAI
from ..services import (
    BlobStorageService,
    PDFProcessingService,
    EntityExtractionService,
    EmbeddingService,
    SearchService,
)
from ..config import settings


def get_blob_service() -> BlobStorageService:
    """Get BlobStorageService instance."""
    return BlobStorageService()


def get_pdf_service() -> PDFProcessingService:
    """Get PDFProcessingService instance."""
    return PDFProcessingService()


def get_entity_service() -> EntityExtractionService:
    """Get EntityExtractionService instance."""
    return EntityExtractionService()


def get_embedding_service() -> EmbeddingService:
    """Get EmbeddingService instance."""
    return EmbeddingService()


def get_search_service() -> SearchService:
    """Get SearchService instance."""
    return SearchService()


def get_openai_client() -> AzureOpenAI:
    """Get OpenAI client instance."""
    return AzureOpenAI(
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        azure_endpoint=settings.azure_openai_endpoint
    )
