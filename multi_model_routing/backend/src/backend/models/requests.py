"""Request models."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class Message(BaseModel):
    """Chat message."""

    role: Literal["system", "user", "assistant", "tool"]
    content: str | list[dict[str, Any]] | None = None
    name: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None


class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible chat completion request."""

    model: str | None = None  # If None, auto-route
    messages: list[Message]
    temperature: float = Field(default=1.0, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    n: int = Field(default=1, ge=1, le=10)
    stream: bool = False
    stop: str | list[str] | None = None
    max_tokens: int | None = None
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    user: str | None = None

    # Routing options
    routing_options: "RoutingOptions | None" = None


class RoutingOptions(BaseModel):
    """Options for query routing."""

    force_tier: Literal["frontier", "standard", "fast"] | None = None
    force_model: str | None = None
    max_cost: float | None = None  # Maximum cost per request
    prefer_provider: Literal["azure_openai", "anthropic"] | None = None


class RoutingPreviewRequest(BaseModel):
    """Request to preview routing decision without executing."""

    messages: list[Message]
    routing_options: RoutingOptions | None = None


class BudgetUpdateRequest(BaseModel):
    """Request to update budget configuration."""

    daily_limit: float | None = Field(default=None, ge=0)
    weekly_limit: float | None = Field(default=None, ge=0)
    monthly_limit: float | None = Field(default=None, ge=0)
    alert_thresholds: list[float] | None = Field(default=None)  # e.g., [0.5, 0.75, 0.9]
    hard_limit: bool | None = None  # Whether to enforce hard limits
