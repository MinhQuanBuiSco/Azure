"""Audit log models."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class AuditLogCreate(BaseModel):
    """Model for creating audit log entries."""

    request_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    client_ip: str | None = None
    user_id: str | None = None
    api_key_id: str | None = None

    # Request details
    endpoint: str
    method: str
    model: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None

    # Security scan results
    security_scan_performed: bool = True
    threats_detected: list[dict[str, Any]] = Field(default_factory=list)
    pii_detected: list[dict[str, Any]] = Field(default_factory=list)
    secrets_detected: list[dict[str, Any]] = Field(default_factory=list)
    content_filtered: bool = False

    # Request status
    status: Literal["allowed", "blocked", "filtered", "error"] = "allowed"
    block_reason: str | None = None
    response_time_ms: float | None = None

    # Raw data (optional, can be disabled for privacy)
    request_hash: str | None = None
    response_hash: str | None = None


class AuditLog(AuditLogCreate):
    """Full audit log model with ID."""

    id: str


class AuditLogQuery(BaseModel):
    """Query parameters for audit logs."""

    start_date: datetime | None = None
    end_date: datetime | None = None
    status: Literal["allowed", "blocked", "filtered", "error"] | None = None
    user_id: str | None = None
    has_threats: bool | None = None
    has_pii: bool | None = None
    model: str | None = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
    sort_by: str = "timestamp"
    sort_order: Literal["asc", "desc"] = "desc"


class AuditLogSummary(BaseModel):
    """Summary statistics for audit logs."""

    total_requests: int = 0
    allowed_requests: int = 0
    blocked_requests: int = 0
    filtered_requests: int = 0
    error_requests: int = 0

    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0

    threats_detected_count: int = 0
    pii_detected_count: int = 0
    secrets_detected_count: int = 0

    avg_response_time_ms: float = 0.0

    # Time range
    start_date: datetime | None = None
    end_date: datetime | None = None
