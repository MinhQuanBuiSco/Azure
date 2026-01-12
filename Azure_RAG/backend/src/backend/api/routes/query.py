import logging
from fastapi import APIRouter, HTTPException, Depends
from openai import AzureOpenAI
from ...models.search_request import SearchRequest, SearchResponse
from ...models.schemas import QueryRequest, QueryResponse
from ...services import SearchService, cache_service
from ...config import settings
from ..dependencies import get_search_service, get_openai_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/query", tags=["query"])


@router.post("/search", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    search_service: SearchService = Depends(get_search_service)
):
    """
    Search documents using specified strategy.

    Args:
        request: Search request with query, strategy, and filters

    Returns:
        Search results
    """
    try:
        # Check cache first
        cache_key_data = {
            "query": request.query,
            "strategy": request.strategy.value,
            "filters": request.entity_filters.dict() if request.entity_filters else None,
            "top_k": request.top_k
        }

        cached_results = await cache_service.get_cached_results(
            query=request.query,
            strategy=request.strategy.value,
            filters=cache_key_data.get("filters")
        )

        if cached_results:
            logger.info("Returning cached search results")
            return SearchResponse(**cached_results, cache_hit=True)

        # Perform search
        logger.info(f"Searching with strategy: {request.strategy.value}")
        results = await search_service.search(request)

        # Build response
        response = SearchResponse(
            query=request.query,
            strategy=request.strategy,
            results=results,
            total_found=len(results),
            cache_hit=False
        )

        # Cache the results
        await cache_service.cache_results(
            query=request.query,
            strategy=request.strategy.value,
            results=response.dict(exclude={"cache_hit"}),
            filters=cache_key_data.get("filters")
        )

        return response

    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/rag", response_model=QueryResponse)
async def rag_query(
    request: QueryRequest,
    search_service: SearchService = Depends(get_search_service),
    openai_client: AzureOpenAI = Depends(get_openai_client)
):
    """
    Perform RAG query: retrieve relevant chunks and generate answer.

    Args:
        request: RAG query request

    Returns:
        Generated answer with sources
    """
    try:
        # Create search request
        search_req = SearchRequest(
            query=request.query,
            strategy="hybrid",  # Use hybrid for RAG
            top_k=5
        )

        # Check cache first
        cache_key = f"rag:{request.query}"
        cached_answer = await cache_service.get_cached_results(
            query=cache_key,
            strategy="rag",
            filters=None
        )

        if cached_answer:
            logger.info("Returning cached RAG answer")
            return QueryResponse(**cached_answer, cache_hit=True)

        # Retrieve relevant chunks
        logger.info(f"Retrieving chunks for query: {request.query}")
        results = await search_service.search(search_req)

        if not results:
            return QueryResponse(
                query=request.query,
                answer="I couldn't find any relevant information to answer your question.",
                sources=[],
                confidence=0.0,
                cache_hit=False
            )

        # Build context from retrieved chunks
        context_parts = []
        sources = []

        for i, result in enumerate(results, 1):
            context_parts.append(f"[Source {i}]\n{result.content}")
            sources.append({
                "index": i,
                "content": result.content[:200] + "...",  # Preview
                "metadata": result.metadata,
                "score": result.score,
                "entities": result.entities
            })

        context = "\n\n".join(context_parts)

        # Generate answer using GPT-4o-mini
        logger.info("Generating answer with GPT-4o-mini")

        system_prompt = """You are a helpful AI assistant that answers questions based on the provided context.

Instructions:
1. Answer the question using ONLY the information from the provided sources
2. Be concise and accurate
3. If the context doesn't contain enough information, say so
4. Cite sources using [Source N] notation when referencing information
5. If sources conflict, acknowledge the discrepancy"""

        user_prompt = f"""Context from documents:

{context}

Question: {request.query}

Please provide a clear and accurate answer based on the context above."""

        response = openai_client.chat.completions.create(
            model=settings.azure_openai_chat_deployment,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=800
        )

        answer = response.choices[0].message.content

        # Calculate confidence based on relevance scores
        # Azure AI Search Hybrid RRF scores typically range 0.01-0.05
        # RRF (Reciprocal Rank Fusion) produces normalized scores much lower than pure BM25/vector
        # Use weighted combination: 70% top score + 30% average
        top_score = results[0].score
        avg_score = sum(r.score for r in results) / len(results)
        combined_score = 0.7 * top_score + 0.3 * avg_score

        # Normalize to 0-1 range for RRF hybrid scores
        # Good matches: 0.03-0.05 -> 60-100%
        # Average matches: 0.015-0.03 -> 30-60%
        # Weak matches: < 0.015 -> < 30%
        confidence = min(combined_score / 0.05, 1.0)

        rag_response = QueryResponse(
            query=request.query,
            answer=answer,
            sources=sources,
            confidence=confidence,
            cache_hit=False
        )

        # Cache the RAG response
        await cache_service.cache_results(
            query=cache_key,
            strategy="rag",
            results=rag_response.dict(exclude={"cache_hit"}),
            filters=None
        )

        logger.info("RAG query completed successfully")

        return rag_response

    except Exception as e:
        logger.error(f"RAG query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"RAG query failed: {str(e)}")
