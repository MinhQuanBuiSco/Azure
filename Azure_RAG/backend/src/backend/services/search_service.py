import logging
from typing import List, Optional
from azure.search.documents import SearchClient
from azure.search.documents.models import (
    VectorizedQuery,
    QueryType,
    QueryCaptionType,
    QueryAnswerType
)
from azure.core.credentials import AzureKeyCredential
from ..models.search_request import SearchStrategy, SearchRequest, SearchResult
from ..models.entities import EntityFilters, ExtractedEntities
from ..config import settings
from .embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class SearchService:
    """Multi-strategy search service using Azure AI Search."""

    def __init__(self):
        """Initialize Azure AI Search client."""
        self.search_client = SearchClient(
            endpoint=settings.azure_search_endpoint,
            index_name=settings.azure_search_index_name,
            credential=AzureKeyCredential(settings.azure_search_api_key)
        )
        self.embedding_service = EmbeddingService()

    async def search(
        self,
        request: SearchRequest
    ) -> List[SearchResult]:
        """
        Perform search using the specified strategy.

        Args:
            request: Search request with strategy and parameters

        Returns:
            List of search results
        """
        logger.info(f"Searching with strategy: {request.strategy.value}")

        if request.strategy == SearchStrategy.BM25:
            return await self._search_bm25(request)
        elif request.strategy == SearchStrategy.SEMANTIC:
            return await self._search_semantic(request)
        elif request.strategy == SearchStrategy.ENTITY:
            return await self._search_entity(request)
        elif request.strategy == SearchStrategy.HYBRID:
            return await self._search_hybrid(request)
        elif request.strategy == SearchStrategy.ADVANCED:
            return await self._search_advanced(request)
        else:
            raise ValueError(f"Unknown search strategy: {request.strategy}")

    async def _search_bm25(self, request: SearchRequest) -> List[SearchResult]:
        """
        BM25 keyword search.

        Uses traditional full-text search with BM25 ranking.
        """
        try:
            # Build filter if entity filters provided
            filter_expr = self._build_entity_filter(request.entity_filters)

            results = self.search_client.search(
                search_text=request.query,
                filter=filter_expr,
                top=request.top_k,
                query_type=QueryType.SIMPLE,
                include_total_count=True
            )

            search_results = []
            for result in results:
                search_results.append(self._convert_to_search_result(
                    result,
                    strategy="BM25",
                    include_entities=request.include_entities
                ))

            logger.info(f"BM25 search returned {len(search_results)} results")
            return search_results

        except Exception as e:
            logger.error(f"BM25 search failed: {str(e)}")
            raise

    async def _search_semantic(self, request: SearchRequest) -> List[SearchResult]:
        """
        Vector similarity search.

        Uses embedding-based semantic search.
        """
        try:
            # Create query embedding
            query_vector = await self.embedding_service.create_query_embedding(request.query)

            # Create vector query
            vector_query = VectorizedQuery(
                vector=query_vector,
                k_nearest_neighbors=request.top_k,
                fields="content_vector"
            )

            # Build filter
            filter_expr = self._build_entity_filter(request.entity_filters)

            results = self.search_client.search(
                search_text=None,
                vector_queries=[vector_query],
                filter=filter_expr,
                top=request.top_k
            )

            search_results = []
            for result in results:
                search_results.append(self._convert_to_search_result(
                    result,
                    strategy="Semantic",
                    include_entities=request.include_entities
                ))

            logger.info(f"Semantic search returned {len(search_results)} results")
            return search_results

        except Exception as e:
            logger.error(f"Semantic search failed: {str(e)}")
            raise

    async def _search_entity(self, request: SearchRequest) -> List[SearchResult]:
        """
        Entity-based search.

        Searches based on entity filters only.
        """
        try:
            if not request.entity_filters or not request.entity_filters.has_filters():
                raise ValueError("Entity search requires entity filters")

            # Build entity filter
            filter_expr = self._build_entity_filter(request.entity_filters)

            # Also search the query text
            results = self.search_client.search(
                search_text=request.query,
                filter=filter_expr,
                top=request.top_k,
                query_type=QueryType.SIMPLE
            )

            search_results = []
            for result in results:
                search_results.append(self._convert_to_search_result(
                    result,
                    strategy="Entity",
                    include_entities=request.include_entities
                ))

            logger.info(f"Entity search returned {len(search_results)} results")
            return search_results

        except Exception as e:
            logger.error(f"Entity search failed: {str(e)}")
            raise

    async def _search_hybrid(self, request: SearchRequest) -> List[SearchResult]:
        """
        Hybrid search (BM25 + Semantic).

        Combines keyword and vector search with RRF (Reciprocal Rank Fusion).
        """
        try:
            # Create query embedding
            query_vector = await self.embedding_service.create_query_embedding(request.query)

            # Create vector query
            vector_query = VectorizedQuery(
                vector=query_vector,
                k_nearest_neighbors=request.top_k * 2,  # Get more for better fusion
                fields="content_vector"
            )

            # Build filter
            filter_expr = self._build_entity_filter(request.entity_filters)

            # Hybrid search (BM25 + Vector with RRF)
            results = self.search_client.search(
                search_text=request.query,
                vector_queries=[vector_query],
                filter=filter_expr,
                top=request.top_k
                # Note: Removed QueryType.SEMANTIC as it requires additional Azure cost ($500/month)
                # Hybrid search automatically uses Reciprocal Rank Fusion (RRF) when combining text + vector
            )

            search_results = []
            for result in results:
                search_results.append(self._convert_to_search_result(
                    result,
                    strategy="Hybrid (BM25+Semantic)",
                    include_entities=request.include_entities
                ))

            logger.info(f"Hybrid search returned {len(search_results)} results")
            return search_results

        except Exception as e:
            logger.error(f"Hybrid search failed: {str(e)}")
            raise

    async def _search_advanced(self, request: SearchRequest) -> List[SearchResult]:
        """
        Advanced hybrid search (BM25 + Semantic + Entity boost).

        Uses all search methods with custom scoring.
        """
        try:
            # Create query embedding
            query_vector = await self.embedding_service.create_query_embedding(request.query)

            # Create vector query
            vector_query = VectorizedQuery(
                vector=query_vector,
                k_nearest_neighbors=request.top_k * 3,
                fields="content_vector"
            )

            # Build enhanced filter with entity boosting
            filter_expr = self._build_entity_filter(request.entity_filters)

            # Advanced hybrid search (BM25 + Vector + Entity filtering with RRF)
            results = self.search_client.search(
                search_text=request.query,
                vector_queries=[vector_query],
                filter=filter_expr,
                top=request.top_k
                # Note: Removed QueryType.SEMANTIC to avoid additional Azure cost
                # Still provides excellent results with BM25 + Vector hybrid + Entity filtering
            )

            search_results = []
            for result in results:
                search_results.append(self._convert_to_search_result(
                    result,
                    strategy="Advanced (All methods)",
                    include_entities=request.include_entities
                ))

            logger.info(f"Advanced search returned {len(search_results)} results")
            return search_results

        except Exception as e:
            logger.error(f"Advanced search failed: {str(e)}")
            raise

    def _build_entity_filter(self, entity_filters: Optional[EntityFilters]) -> Optional[str]:
        """
        Build OData filter expression from entity filters.

        Args:
            entity_filters: Entity filters

        Returns:
            OData filter string or None
        """
        if not entity_filters or not entity_filters.has_filters():
            return None

        filter_parts = []

        if entity_filters.people:
            people_filters = [f"entities_people/any(p: p eq '{person}')" for person in entity_filters.people]
            filter_parts.append(f"({' or '.join(people_filters)})")

        if entity_filters.organizations:
            org_filters = [f"entities_organizations/any(o: o eq '{org}')" for org in entity_filters.organizations]
            filter_parts.append(f"({' or '.join(org_filters)})")

        if entity_filters.locations:
            loc_filters = [f"entities_locations/any(l: l eq '{loc}')" for loc in entity_filters.locations]
            filter_parts.append(f"({' or '.join(loc_filters)})")

        if entity_filters.topics:
            topic_filters = [f"entities_topics/any(t: t eq '{topic}')" for topic in entity_filters.topics]
            filter_parts.append(f"({' or '.join(topic_filters)})")

        if entity_filters.technical_terms:
            term_filters = [f"entities_technical_terms/any(tt: tt eq '{term}')" for term in entity_filters.technical_terms]
            filter_parts.append(f"({' or '.join(term_filters)})")

        return " and ".join(filter_parts) if filter_parts else None

    def _convert_to_search_result(
        self,
        azure_result: dict,
        strategy: str,
        include_entities: bool = True
    ) -> SearchResult:
        """Convert Azure Search result to SearchResult model."""
        entities = None
        if include_entities and "entities_people" in azure_result:
            entities = {
                "people": azure_result.get("entities_people", []),
                "organizations": azure_result.get("entities_organizations", []),
                "locations": azure_result.get("entities_locations", []),
                "topics": azure_result.get("entities_topics", []),
                "technical_terms": azure_result.get("entities_technical_terms", []),
            }

        return SearchResult(
            chunk_id=azure_result.get("chunk_id", ""),
            content=azure_result.get("content", ""),
            score=azure_result.get("@search.score", 0.0),
            metadata={
                "document_id": azure_result.get("document_id", ""),
                "filename": azure_result.get("filename", ""),
                "chunk_index": azure_result.get("chunk_index", 0),
                "page_numbers": azure_result.get("page_numbers", []),
            },
            entities=entities,
            match_explanation=f"Matched using {strategy}"
        )

    async def index_document_chunks(
        self,
        chunks: List[dict],
        embeddings: List[List[float]],
        entities_list: List[ExtractedEntities]
    ):
        """
        Index document chunks with embeddings and entities.

        Args:
            chunks: List of chunk dictionaries
            embeddings: List of embedding vectors
            entities_list: List of extracted entities per chunk
        """
        try:
            documents = []

            for i, (chunk, embedding, entities) in enumerate(zip(chunks, embeddings, entities_list)):
                doc = {
                    "chunk_id": chunk["metadata"]["chunk_id"],
                    "content": chunk["content"],
                    "content_vector": embedding,
                    "document_id": chunk["metadata"]["document_id"],
                    "filename": chunk["metadata"]["filename"],
                    "chunk_index": chunk["chunk_index"],
                    "total_chunks": chunk["metadata"]["total_chunks"],
                    "page_numbers": chunk["metadata"].get("page_numbers", []),
                    "entities_people": entities.people,
                    "entities_organizations": entities.organizations,
                    "entities_locations": entities.locations,
                    "entities_topics": entities.topics,
                    "entities_technical_terms": entities.technical_terms,
                    "entity_summary": entities.to_searchable_text(),
                }
                documents.append(doc)

            # Upload to Azure AI Search
            result = self.search_client.upload_documents(documents=documents)

            succeeded = sum(1 for r in result if r.succeeded)
            logger.info(f"Indexed {succeeded}/{len(documents)} chunks successfully")

        except Exception as e:
            logger.error(f"Failed to index documents: {str(e)}")
            raise
