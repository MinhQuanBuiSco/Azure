"""Response models."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class Usage(BaseModel):
    """Token usage information."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class Choice(BaseModel):
    """Chat completion choice."""

    index: int
    message: dict[str, Any]
    finish_reason: str | None = None


class RoutingDecision(BaseModel):
    """Information about the routing decision made."""

    selected_model: str
    selected_tier: str
    complexity_score: int
    query_category: str
    estimated_cost: float
    routing_reason: str


class ChatCompletionResponse(BaseModel):
    """OpenAI-compatible chat completion response."""

    id: str
    object: Literal["chat.completion"] = "chat.completion"
    created: int
    model: str
    choices: list[Choice]
    usage: Usage | None = None

    # Extended routing info
    routing: RoutingDecision | None = None


class StreamDelta(BaseModel):
    """Delta for streaming response."""

    role: str | None = None
    content: str | None = None


class StreamChoice(BaseModel):
    """Streaming choice."""

    index: int
    delta: StreamDelta
    finish_reason: str | None = None


class ChatCompletionChunk(BaseModel):
    """Streaming chat completion chunk."""

    id: str
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    created: int
    model: str
    choices: list[StreamChoice]


class RoutingPreviewResponse(BaseModel):
    """Response for routing preview."""

    decision: RoutingDecision
    alternative_options: list[dict[str, Any]] = Field(default_factory=list)
    complexity_breakdown: dict[str, float] = Field(default_factory=dict)


class CostAnalytics(BaseModel):
    """Cost analytics response."""

    period: str  # daily, weekly, monthly
    start_date: datetime
    end_date: datetime
    total_cost: float
    total_requests: int
    cost_by_tier: dict[str, float]
    cost_by_model: dict[str, float]
    average_cost_per_request: float


class SavingsAnalytics(BaseModel):
    """Savings analytics compared to always using frontier."""

    period: str
    start_date: datetime
    end_date: datetime
    actual_cost: float
    frontier_cost: float  # What it would have cost with frontier only
    savings: float
    savings_percentage: float
    requests_routed_to_lower_tiers: int
    total_requests: int


class BudgetStatus(BaseModel):
    """Current budget status."""

    user_id: str
    daily_limit: float
    daily_spent: float
    daily_remaining: float
    weekly_limit: float
    weekly_spent: float
    weekly_remaining: float
    monthly_limit: float
    monthly_spent: float
    monthly_remaining: float
    alerts: list[str] = Field(default_factory=list)
    is_limited: bool = False  # Whether requests are being blocked


class HealthResponse(BaseModel):
    """Health check response."""

    status: Literal["healthy", "degraded", "unhealthy"]
    version: str
    environment: str
    services: dict[str, bool] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Error response."""

    error: str
    detail: str | None = None
    code: str | None = None
