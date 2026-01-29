"""Chat completion endpoints with routing."""

import logging
import time
import uuid
from typing import Any, AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from backend.config import Settings, get_settings, calculate_cost, MODELS
from backend.models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    Choice,
    RoutingDecision,
    RoutingPreviewRequest,
    RoutingPreviewResponse,
    Usage,
)
from backend.providers import AzureOpenAIProvider
from backend.routing import get_router
from backend.budget import BudgetController
from backend.storage import get_redis_client, get_cosmos_client

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


def get_budget_controller(settings: Settings = Depends(get_settings)) -> BudgetController:
    """Get budget controller instance."""
    redis = get_redis_client(settings)
    cosmos = get_cosmos_client(settings)
    return BudgetController(settings, redis, cosmos)


@router.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(
    request: ChatCompletionRequest,
    http_request: Request,
    settings: Settings = Depends(get_settings),
    budget_controller: BudgetController = Depends(get_budget_controller),
) -> ChatCompletionResponse | StreamingResponse:
    """
    OpenAI-compatible chat completions endpoint with intelligent routing.

    If no model is specified, automatically routes to the optimal model
    based on query complexity and semantic classification.
    """
    start_time = time.time()
    request_id = str(uuid.uuid4())

    # Get user ID from header or default
    user_id = http_request.headers.get("X-User-ID", "default")

    # Get router
    llm_router = get_router()

    # Determine routing
    if request.model and request.model in MODELS:
        # Use specified model directly
        model_config = MODELS[request.model]
        routing_decision = RoutingDecision(
            selected_model=model_config.id,
            selected_tier=model_config.tier.value,
            complexity_score=0,
            query_category="specified",
            estimated_cost=0.0,
            routing_reason=f"Model '{request.model}' explicitly specified",
        )
    else:
        # Auto-route based on query analysis
        routing_result = llm_router.route(request.messages, request.routing_options)
        routing_decision = llm_router.to_routing_decision(routing_result)
        model_config = routing_result.selection.model

    # Check budget
    budget_check = await budget_controller.check_budget(
        user_id, routing_decision.estimated_cost
    )

    if not budget_check.allowed:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "budget_exceeded",
                "message": budget_check.reason,
                "alerts": budget_check.alerts,
            },
        )

    # Select provider
    provider = AzureOpenAIProvider(settings)

    try:
        # Make the request
        if request.stream:
            return StreamingResponse(
                _stream_response(
                    provider=provider,
                    request=request,
                    model_config=model_config,
                    routing_decision=routing_decision,
                    user_id=user_id,
                    request_id=request_id,
                    start_time=start_time,
                    budget_controller=budget_controller,
                    settings=settings,
                ),
                media_type="text/event-stream",
            )

        response = await provider.chat_completion(
            messages=request.messages,
            model=model_config.id,
            temperature=request.temperature,
            max_tokens=request.max_tokens or model_config.max_tokens,
            stream=False,
            top_p=request.top_p,
            presence_penalty=request.presence_penalty,
            frequency_penalty=request.frequency_penalty,
            stop=request.stop,
        )

        # Calculate actual cost
        usage = response.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        actual_cost = calculate_cost(model_config.id, input_tokens, output_tokens)

        # Record spend
        await budget_controller.record_spend(user_id, actual_cost)

        # Log to storage
        latency_ms = int((time.time() - start_time) * 1000)
        redis = get_redis_client(settings)
        await redis.record_request(
            user_id=user_id,
            model=model_config.id,
            tier=model_config.tier.value,
            cost=actual_cost,
            latency_ms=latency_ms,
        )

        # Log to Cosmos DB for analytics
        try:
            cosmos = get_cosmos_client(settings)
            await cosmos.log_routing_decision(
                user_id=user_id,
                request_id=request_id,
                model=model_config.id,
                tier=model_config.tier.value,
                complexity_score=routing_decision.complexity_score,
                category=routing_decision.query_category,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=actual_cost,
                latency_ms=latency_ms,
                routing_reason=routing_decision.routing_reason,
            )
        except Exception as e:
            logger.warning(f"Failed to log routing decision to Cosmos DB: {e}")

        # Update routing decision with actual cost
        routing_decision.estimated_cost = round(actual_cost, 6)

        # Format response
        return ChatCompletionResponse(
            id=response.get("id", request_id),
            created=response.get("created", int(time.time())),
            model=model_config.id,
            choices=[
                Choice(
                    index=c["index"],
                    message=c["message"],
                    finish_reason=c.get("finish_reason"),
                )
                for c in response.get("choices", [])
            ],
            usage=Usage(
                prompt_tokens=input_tokens,
                completion_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
            ),
            routing=routing_decision,
        )

    except Exception as e:
        logger.error(f"Chat completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await provider.close()


async def _stream_response(
    provider: Any,
    request: ChatCompletionRequest,
    model_config: Any,
    routing_decision: RoutingDecision,
    user_id: str,
    request_id: str,
    start_time: float,
    budget_controller: BudgetController,
    settings: Settings,
) -> AsyncIterator[str]:
    """Stream chat completion response."""
    import json

    try:
        stream = await provider.chat_completion(
            messages=request.messages,
            model=model_config.id,
            temperature=request.temperature,
            max_tokens=request.max_tokens or model_config.max_tokens,
            stream=True,
            top_p=request.top_p,
            presence_penalty=request.presence_penalty,
            frequency_penalty=request.frequency_penalty,
            stop=request.stop,
        )

        total_content = ""
        async for chunk in stream:
            # Extract content for token estimation
            for choice in chunk.get("choices", []):
                delta = choice.get("delta", {})
                if delta.get("content"):
                    total_content += delta["content"]

            # Send chunk
            yield f"data: {json.dumps(chunk)}\n\n"

        # Estimate tokens and record cost
        # Rough estimation since streaming doesn't provide token counts
        input_tokens = sum(
            len(str(m.content or "")) // 4 for m in request.messages
        )
        output_tokens = len(total_content) // 4

        actual_cost = calculate_cost(model_config.id, input_tokens, output_tokens)
        await budget_controller.record_spend(user_id, actual_cost)

        # Record metrics
        latency_ms = int((time.time() - start_time) * 1000)
        redis = get_redis_client(settings)
        await redis.record_request(
            user_id=user_id,
            model=model_config.id,
            tier=model_config.tier.value,
            cost=actual_cost,
            latency_ms=latency_ms,
        )

        # Log to Cosmos DB for analytics
        try:
            cosmos = get_cosmos_client(settings)
            await cosmos.log_routing_decision(
                user_id=user_id,
                request_id=request_id,
                model=model_config.id,
                tier=model_config.tier.value,
                complexity_score=routing_decision.complexity_score,
                category=routing_decision.query_category,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=actual_cost,
                latency_ms=latency_ms,
                routing_reason=routing_decision.routing_reason,
            )
        except Exception as e:
            logger.warning(f"Failed to log routing decision to Cosmos DB: {e}")

        # Send final chunk with routing decision and usage info
        final_chunk = {
            "id": request_id,
            "object": "chat.completion.chunk",
            "model": model_config.id,
            "choices": [],
            "routing": {
                "selected_model": routing_decision.selected_model,
                "selected_tier": routing_decision.selected_tier,
                "complexity_score": routing_decision.complexity_score,
                "query_category": routing_decision.query_category,
                "estimated_cost": actual_cost,
                "routing_reason": routing_decision.routing_reason,
            },
            "usage": {
                "prompt_tokens": input_tokens,
                "completion_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
            },
        }
        yield f"data: {json.dumps(final_chunk)}\n\n"

        yield "data: [DONE]\n\n"

    except Exception as e:
        logger.error(f"Streaming error: {e}")
        error_chunk = {
            "error": {"message": str(e), "type": "server_error"}
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"
    finally:
        await provider.close()


@router.post("/api/routing/preview", response_model=RoutingPreviewResponse)
async def preview_routing(
    request: RoutingPreviewRequest,
    settings: Settings = Depends(get_settings),
) -> RoutingPreviewResponse:
    """
    Preview routing decision without executing the request.

    Useful for understanding how queries will be routed and their estimated costs.
    """
    llm_router = get_router()

    decision, complexity_breakdown, alternatives = llm_router.preview(
        request.messages, request.routing_options
    )

    return RoutingPreviewResponse(
        decision=decision,
        complexity_breakdown=complexity_breakdown,
        alternative_options=alternatives,
    )
