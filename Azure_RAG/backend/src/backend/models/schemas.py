from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from datetime import datetime


class IndexingStatus(str, Enum):
    """Document indexing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    EXTRACTING_ENTITIES = "extracting_entities"
    EMBEDDING = "embedding"
    INDEXING = "indexing"
    COMPLETED = "completed"
    FAILED = "failed"


class UploadResponse(BaseModel):
    """Response after PDF upload."""

    document_id: str
    filename: str
    size_bytes: int
    blob_url: str
    message: str = "File uploaded successfully"


class IndexRequest(BaseModel):
    """Request to start indexing a document."""

    document_id: str
    extract_entities: bool = Field(default=True, description="Enable entity extraction")


class IndexingProgress(BaseModel):
    """Indexing progress information."""

    document_id: str
    status: IndexingStatus
    progress_percentage: int = Field(ge=0, le=100)
    current_step: str
    total_chunks: Optional[int] = None
    processed_chunks: Optional[int] = None
    entities_extracted: Optional[int] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class QueryRequest(BaseModel):
    """RAG query request with streaming support."""

    query: str = Field(..., min_length=1, max_length=1000)
    document_ids: Optional[list[str]] = Field(
        default=None,
        description="Optional list of document IDs to search within"
    )
    stream: bool = Field(default=False, description="Stream the response")


class QueryResponse(BaseModel):
    """RAG query response."""

    query: str
    answer: str
    sources: list[dict]
    confidence: Optional[float] = None
    cache_hit: bool = False


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str
    services: dict[str, str]
