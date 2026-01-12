from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional
from .entities import EntityFilters


class SearchStrategy(str, Enum):
    """Available search strategies."""

    BM25 = "bm25"  # Traditional keyword search
    SEMANTIC = "semantic"  # Vector similarity search
    ENTITY = "entity"  # Entity-based filtering
    HYBRID = "hybrid"  # BM25 + Semantic (default)
    ADVANCED = "advanced"  # BM25 + Semantic + Entity boost


class SearchRequest(BaseModel):
    """Request model for RAG query."""

    query: str = Field(..., min_length=1, max_length=1000, description="User query text")
    strategy: SearchStrategy = Field(
        default=SearchStrategy.HYBRID,
        description="Search strategy to use"
    )
    entity_filters: Optional[EntityFilters] = Field(
        default=None,
        description="Optional entity filters to apply"
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of results to retrieve"
    )
    include_entities: bool = Field(
        default=True,
        description="Include extracted entities in response"
    )


class SearchResult(BaseModel):
    """Single search result."""

    chunk_id: str
    content: str
    score: float
    metadata: dict
    entities: Optional[dict] = None
    match_explanation: Optional[str] = None


class SearchResponse(BaseModel):
    """Response model for search results."""

    query: str
    strategy: SearchStrategy
    results: list[SearchResult]
    total_found: int
    cache_hit: bool = False
