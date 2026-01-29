"""Main routing orchestrator."""

import hashlib
import json
import logging
from dataclasses import dataclass
from typing import Any, Literal

from backend.config import ModelTier, QueryCategory, calculate_cost
from backend.models import Message, RoutingDecision, RoutingOptions
from backend.routing.complexity_analyzer import ComplexityAnalyzer, ComplexityBreakdown
from backend.routing.model_selector import ModelSelector, SelectionResult
from backend.routing.semantic_router import SemanticRouter, get_semantic_router

logger = logging.getLogger(__name__)


@dataclass
class RoutingResult:
    """Complete routing result."""

    selection: SelectionResult
    complexity_breakdown: ComplexityBreakdown
    category_scores: dict[str, float]
    cache_key: str | None = None


class Router:
    """Main routing orchestrator that combines all routing components."""

    def __init__(
        self,
        enable_caching: bool = True,
    ) -> None:
        """Initialize the router with all components."""
        self._complexity_analyzer = ComplexityAnalyzer()
        self._semantic_router = get_semantic_router()
        self._model_selector = ModelSelector()
        self._enable_caching = enable_caching
        self._cache: dict[str, RoutingResult] = {}  # Simple in-memory cache

    def _compute_cache_key(self, messages: list[dict]) -> str:
        """Compute a cache key for the messages."""
        # Use last user message for cache key
        user_messages = [m for m in messages if m.get("role") == "user"]
        if not user_messages:
            return ""

        last_message = user_messages[-1].get("content", "")
        if isinstance(last_message, list):
            # Handle multi-modal content
            text_parts = [
                p.get("text", "") for p in last_message if isinstance(p, dict) and p.get("type") == "text"
            ]
            last_message = " ".join(text_parts)

        return hashlib.sha256(last_message.encode()).hexdigest()[:16]

    def _messages_to_dicts(self, messages: list[Message]) -> list[dict[str, Any]]:
        """Convert Message objects to dictionaries."""
        return [m.model_dump(exclude_none=True) for m in messages]

    def route(
        self,
        messages: list[Message],
        options: RoutingOptions | None = None,
    ) -> RoutingResult:
        """
        Route a query to the optimal model.

        Args:
            messages: Chat messages
            options: Optional routing options

        Returns:
            RoutingResult with full routing decision
        """
        message_dicts = self._messages_to_dicts(messages)

        # Check cache
        cache_key = self._compute_cache_key(message_dicts) if self._enable_caching else None
        if cache_key and cache_key in self._cache:
            logger.debug(f"Cache hit for key: {cache_key}")
            return self._cache[cache_key]

        # Extract text from the last user message for routing decisions.
        # Using only the latest user message avoids prior conversation
        # history (e.g. a math question) from polluting routing for a
        # simple follow-up like "Hello".
        user_messages = [m for m in message_dicts if m.get("role") == "user"]
        if user_messages:
            last_user = user_messages[-1]
            text = self._complexity_analyzer.get_messages_text([last_user])
        else:
            text = self._complexity_analyzer.get_messages_text(message_dicts)

        # Analyze complexity
        complexity = self._complexity_analyzer.analyze(text)
        logger.debug(f"Complexity score: {complexity.total_score}")

        # Classify semantically
        category, category_scores = self._semantic_router.classify(text)
        logger.debug(f"Category: {category.value}, scores: {category_scores}")

        # Parse routing options
        force_tier: ModelTier | None = None
        force_model: str | None = None
        prefer_provider: Literal["azure_openai", "anthropic"] | None = None
        max_cost: float | None = None

        if options:
            if options.force_tier:
                force_tier = ModelTier(options.force_tier)
            force_model = options.force_model
            prefer_provider = options.prefer_provider
            max_cost = options.max_cost

        # Select model
        selection = self._model_selector.select(
            complexity_score=complexity.total_score,
            category=category,
            messages=message_dicts,
            force_tier=force_tier,
            force_model=force_model,
            prefer_provider=prefer_provider,
            max_cost=max_cost,
        )

        result = RoutingResult(
            selection=selection,
            complexity_breakdown=complexity,
            category_scores=category_scores,
            cache_key=cache_key,
        )

        # Cache result
        if cache_key:
            self._cache[cache_key] = result
            # Limit cache size
            if len(self._cache) > 1000:
                # Remove oldest entries
                keys = list(self._cache.keys())
                for k in keys[:500]:
                    del self._cache[k]

        return result

    def to_routing_decision(self, result: RoutingResult) -> RoutingDecision:
        """Convert routing result to API response format."""
        estimated_cost = calculate_cost(
            result.selection.model.id,
            result.selection.estimated_input_tokens,
            result.selection.estimated_output_tokens,
        )

        return RoutingDecision(
            selected_model=result.selection.model.id,
            selected_tier=result.selection.tier.value,
            complexity_score=result.selection.complexity_score,
            query_category=result.selection.category.value,
            estimated_cost=round(estimated_cost, 6),
            routing_reason=result.selection.reason,
        )

    def preview(
        self,
        messages: list[Message],
        options: RoutingOptions | None = None,
    ) -> tuple[RoutingDecision, dict[str, float], list[dict[str, Any]]]:
        """
        Preview routing decision without executing.

        Returns:
            Tuple of (decision, complexity_breakdown, alternative_options)
        """
        result = self.route(messages, options)
        decision = self.to_routing_decision(result)

        # Generate alternative options
        alternatives = []
        for tier in ModelTier:
            if tier != result.selection.tier:
                from backend.config import DEFAULT_MODELS, MODELS

                model_id = DEFAULT_MODELS.get(tier)
                if model_id and model_id in MODELS:
                    model = MODELS[model_id]
                    est_cost = calculate_cost(
                        model.id,
                        result.selection.estimated_input_tokens,
                        result.selection.estimated_output_tokens,
                    )
                    alternatives.append(
                        {
                            "model": model.id,
                            "tier": tier.value,
                            "estimated_cost": round(est_cost, 6),
                        }
                    )

        return decision, result.complexity_breakdown.to_dict(), alternatives

    def clear_cache(self) -> None:
        """Clear the routing cache."""
        self._cache.clear()


# Global router instance
_router: Router | None = None


def get_router() -> Router:
    """Get or create the global router instance."""
    global _router
    if _router is None:
        _router = Router()
    return _router
