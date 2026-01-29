"""Model configuration and pricing."""

from dataclasses import dataclass
from enum import Enum
from typing import Literal


class ModelTier(str, Enum):
    """Model tier classification."""

    FRONTIER = "frontier"
    STANDARD = "standard"
    FAST = "fast"


class QueryCategory(str, Enum):
    """Query semantic classification."""

    CHAT = "chat"
    QA = "qa"
    CODING = "coding"
    REASONING = "reasoning"
    CREATIVE = "creative"
    MATH = "math"
    RESEARCH = "research"


@dataclass(frozen=True)
class ModelPricing:
    """Pricing per 1M tokens."""

    input_cost: float  # $ per 1M input tokens
    output_cost: float  # $ per 1M output tokens


@dataclass(frozen=True)
class ModelConfig:
    """Model configuration."""

    id: str
    name: str
    provider: Literal["azure_openai"]
    tier: ModelTier
    pricing: ModelPricing
    deployment_name: str | None = None  # For Azure OpenAI / Foundry
    max_tokens: int = 4096
    supports_streaming: bool = True
    supports_function_calling: bool = True


# Model definitions
MODELS: dict[str, ModelConfig] = {
    # Frontier tier
    "gpt-4.1": ModelConfig(
        id="gpt-4.1",
        name="GPT-4.1",
        provider="azure_openai",
        tier=ModelTier.FRONTIER,
        pricing=ModelPricing(input_cost=2.0, output_cost=8.0),
        deployment_name="gpt-4.1",
        max_tokens=32768,
    ),
    # Standard tier
    "gpt-4.1-mini": ModelConfig(
        id="gpt-4.1-mini",
        name="GPT-4.1 Mini",
        provider="azure_openai",
        tier=ModelTier.STANDARD,
        pricing=ModelPricing(input_cost=0.40, output_cost=1.60),
        deployment_name="gpt-4.1-mini",
        max_tokens=32768,
    ),
    # Fast tier
    "gpt-4.1-nano": ModelConfig(
        id="gpt-4.1-nano",
        name="GPT-4.1 Nano",
        provider="azure_openai",
        tier=ModelTier.FAST,
        pricing=ModelPricing(input_cost=0.10, output_cost=0.40),
        deployment_name="gpt-4.1-nano",
        max_tokens=32768,
    ),
}

# Default model per tier
DEFAULT_MODELS: dict[ModelTier, str] = {
    ModelTier.FRONTIER: "gpt-4.1",
    ModelTier.STANDARD: "gpt-4.1-mini",
    ModelTier.FAST: "gpt-4.1-nano",
}

# Category to recommended tier mapping
CATEGORY_TIER_MAP: dict[QueryCategory, ModelTier] = {
    QueryCategory.CHAT: ModelTier.FAST,
    QueryCategory.QA: ModelTier.STANDARD,
    QueryCategory.CODING: ModelTier.STANDARD,
    QueryCategory.REASONING: ModelTier.FRONTIER,
    QueryCategory.CREATIVE: ModelTier.STANDARD,
    QueryCategory.MATH: ModelTier.FRONTIER,
    QueryCategory.RESEARCH: ModelTier.FRONTIER,
}

# Complexity thresholds for tier selection
COMPLEXITY_THRESHOLDS: dict[ModelTier, tuple[int, int]] = {
    ModelTier.FAST: (0, 30),
    ModelTier.STANDARD: (31, 70),
    ModelTier.FRONTIER: (71, 100),
}


def get_model(model_id: str) -> ModelConfig | None:
    """Get model configuration by ID."""
    return MODELS.get(model_id)


def get_tier_models(tier: ModelTier) -> list[ModelConfig]:
    """Get all models in a tier."""
    return [m for m in MODELS.values() if m.tier == tier]


def calculate_cost(model_id: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate cost for a request."""
    model = MODELS.get(model_id)
    if not model:
        return 0.0

    input_cost = (input_tokens / 1_000_000) * model.pricing.input_cost
    output_cost = (output_tokens / 1_000_000) * model.pricing.output_cost
    return input_cost + output_cost
