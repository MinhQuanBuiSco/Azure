"""Request and response models for OpenAI-compatible API."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A message in a chat conversation."""

    role: Literal["system", "user", "assistant", "function", "tool"] = "user"
    content: str | list[dict[str, Any]] | None = None
    name: str | None = None
    function_call: dict[str, Any] | None = None
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None


class ChatCompletionRequest(BaseModel):
    """Request model for chat completions."""

    model: str = "gpt-4o"
    messages: list[ChatMessage]
    temperature: float | None = Field(default=1.0, ge=0, le=2)
    top_p: float | None = Field(default=1.0, ge=0, le=1)
    n: int | None = Field(default=1, ge=1, le=10)
    stream: bool | None = False
    stop: str | list[str] | None = None
    max_tokens: int | None = None
    presence_penalty: float | None = Field(default=0, ge=-2, le=2)
    frequency_penalty: float | None = Field(default=0, ge=-2, le=2)
    logit_bias: dict[str, float] | None = None
    user: str | None = None
    functions: list[dict[str, Any]] | None = None
    function_call: str | dict[str, str] | None = None
    tools: list[dict[str, Any]] | None = None
    tool_choice: str | dict[str, Any] | None = None
    response_format: dict[str, str] | None = None
    seed: int | None = None


class Usage(BaseModel):
    """Token usage information."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionChoice(BaseModel):
    """A single completion choice."""

    index: int
    message: ChatMessage
    finish_reason: str | None = None
    logprobs: dict[str, Any] | None = None


class ChatCompletionResponse(BaseModel):
    """Response model for chat completions."""

    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[ChatCompletionChoice]
    usage: Usage | None = None
    system_fingerprint: str | None = None


class CompletionRequest(BaseModel):
    """Request model for text completions."""

    model: str = "gpt-4o"
    prompt: str | list[str]
    suffix: str | None = None
    max_tokens: int | None = Field(default=16, ge=1)
    temperature: float | None = Field(default=1.0, ge=0, le=2)
    top_p: float | None = Field(default=1.0, ge=0, le=1)
    n: int | None = Field(default=1, ge=1)
    stream: bool | None = False
    logprobs: int | None = None
    echo: bool | None = False
    stop: str | list[str] | None = None
    presence_penalty: float | None = Field(default=0, ge=-2, le=2)
    frequency_penalty: float | None = Field(default=0, ge=-2, le=2)
    best_of: int | None = Field(default=1, ge=1)
    logit_bias: dict[str, float] | None = None
    user: str | None = None


class CompletionChoice(BaseModel):
    """A single completion choice."""

    text: str
    index: int
    logprobs: dict[str, Any] | None = None
    finish_reason: str | None = None


class CompletionResponse(BaseModel):
    """Response model for text completions."""

    id: str
    object: str = "text_completion"
    created: int
    model: str
    choices: list[CompletionChoice]
    usage: Usage | None = None
    system_fingerprint: str | None = None


class SecurityBlockedResponse(BaseModel):
    """Response when a request is blocked by security checks."""

    error: dict[str, Any] = Field(
        default_factory=lambda: {
            "message": "Request blocked by security policy",
            "type": "security_violation",
            "code": "content_filter",
        }
    )
    blocked: bool = True
    security_scan: dict[str, Any] | None = None
