"""Model selection logic based on routing signals."""

import logging
from dataclasses import dataclass
from typing import Literal

from backend.config import (
    CATEGORY_TIER_MAP,
    COMPLEXITY_THRESHOLDS,
    DEFAULT_MODELS,
    MODELS,
    ModelConfig,
    ModelTier,
    QueryCategory,
)

logger = logging.getLogger(__name__)


@dataclass
class SelectionResult:
    """Result of model selection."""

    model: ModelConfig
    tier: ModelTier
    reason: str
    complexity_score: int
    category: QueryCategory
    estimated_input_tokens: int
    estimated_output_tokens: int


class ModelSelector:
    """Selects the optimal model based on routing signals."""

    def __init__(self) -> None:
        """Initialize the model selector."""
        pass

    def _get_tier_from_complexity(self, score: int) -> ModelTier:
        """Determine tier based on complexity score."""
        for tier, (low, high) in COMPLEXITY_THRESHOLDS.items():
            if low <= score <= high:
                return tier
        return ModelTier.STANDARD

    def _get_tier_from_category(self, category: QueryCategory) -> ModelTier:
        """Get recommended tier for a category."""
        return CATEGORY_TIER_MAP.get(category, ModelTier.STANDARD)

    def _combine_tier_signals(
        self,
        complexity_tier: ModelTier,
        category_tier: ModelTier,
        complexity_score: int,
    ) -> tuple[ModelTier, str]:
        """
        Combine complexity and category signals to determine final tier.

        Uses a weighted approach favoring complexity for extreme scores.
        """
        tier_order = [ModelTier.FAST, ModelTier.STANDARD, ModelTier.FRONTIER]
        complexity_idx = tier_order.index(complexity_tier)
        category_idx = tier_order.index(category_tier)

        # Strong complexity signal (very low or very high)
        if complexity_score <= 15:
            return ModelTier.FAST, "Very low complexity - simple query"
        if complexity_score >= 85:
            return ModelTier.FRONTIER, "Very high complexity - requires advanced reasoning"

        # Category acts as a minimum tier floor: if the category requires
        # a certain capability level, never route below it regardless of
        # how simple the query appears.
        if category_idx > complexity_idx:
            return (
                category_tier,
                f"Category requires {category_tier.value} model",
            )

        # Average the signals
        avg_idx = (complexity_idx + category_idx) / 2

        if avg_idx < 0.75:
            final_tier = ModelTier.FAST
            reason = "Low complexity and simple category"
        elif avg_idx < 1.5:
            final_tier = ModelTier.STANDARD
            reason = "Moderate complexity - balanced routing"
        else:
            final_tier = ModelTier.FRONTIER
            reason = "High complexity or demanding category"

        return final_tier, reason

    def _select_model_in_tier(
        self,
        tier: ModelTier,
        prefer_provider: Literal["azure_openai", "anthropic"] | None = None,
        max_cost: float | None = None,
    ) -> ModelConfig:
        """Select the best model within a tier."""
        tier_models = [m for m in MODELS.values() if m.tier == tier]

        if not tier_models:
            # Fallback to default
            default_id = DEFAULT_MODELS.get(tier, "gpt-4o-mini")
            return MODELS[default_id]

        # Filter by provider preference
        if prefer_provider:
            preferred = [m for m in tier_models if m.provider == prefer_provider]
            if preferred:
                tier_models = preferred

        # Filter by max cost (using input cost as proxy)
        if max_cost is not None:
            affordable = [m for m in tier_models if m.pricing.input_cost <= max_cost * 1000]
            if affordable:
                tier_models = affordable

        # Sort by cost (cheapest first within tier)
        tier_models.sort(key=lambda m: m.pricing.input_cost)

        return tier_models[0]

    def _estimate_tokens(
        self, messages: list[dict], estimated_response_length: int = 500
    ) -> tuple[int, int]:
        """Estimate input and output tokens."""
        # Rough estimation
        input_chars = sum(
            len(str(m.get("content", "")))
            for m in messages
        )
        input_tokens = int(input_chars / 4)  # Rough char to token ratio

        # Output estimation based on input length and typical response ratio
        output_tokens = min(estimated_response_length, max(100, input_tokens // 2))

        return input_tokens, output_tokens

    def select(
        self,
        complexity_score: int,
        category: QueryCategory,
        messages: list[dict],
        force_tier: ModelTier | None = None,
        force_model: str | None = None,
        prefer_provider: Literal["azure_openai", "anthropic"] | None = None,
        max_cost: float | None = None,
    ) -> SelectionResult:
        """
        Select the optimal model based on routing signals.

        Args:
            complexity_score: 0-100 complexity score
            category: Semantic category of the query
            messages: Chat messages for token estimation
            force_tier: Override tier selection
            force_model: Override model selection
            prefer_provider: Preferred provider
            max_cost: Maximum cost per request

        Returns:
            SelectionResult with chosen model and reasoning
        """
        input_tokens, output_tokens = self._estimate_tokens(messages)

        # Handle forced model
        if force_model and force_model in MODELS:
            model = MODELS[force_model]
            return SelectionResult(
                model=model,
                tier=model.tier,
                reason=f"Forced to use {model.name}",
                complexity_score=complexity_score,
                category=category,
                estimated_input_tokens=input_tokens,
                estimated_output_tokens=output_tokens,
            )

        # Handle forced tier
        if force_tier:
            model = self._select_model_in_tier(force_tier, prefer_provider, max_cost)
            return SelectionResult(
                model=model,
                tier=force_tier,
                reason=f"Forced to tier {force_tier.value}",
                complexity_score=complexity_score,
                category=category,
                estimated_input_tokens=input_tokens,
                estimated_output_tokens=output_tokens,
            )

        # Determine tiers from signals
        complexity_tier = self._get_tier_from_complexity(complexity_score)
        category_tier = self._get_tier_from_category(category)

        # Combine signals
        final_tier, reason = self._combine_tier_signals(
            complexity_tier, category_tier, complexity_score
        )

        # Select model in tier
        model = self._select_model_in_tier(final_tier, prefer_provider, max_cost)

        return SelectionResult(
            model=model,
            tier=final_tier,
            reason=reason,
            complexity_score=complexity_score,
            category=category,
            estimated_input_tokens=input_tokens,
            estimated_output_tokens=output_tokens,
        )
