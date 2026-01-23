"""Security scan result models."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ThreatDetection(BaseModel):
    """Details of a detected threat."""

    type: Literal[
        "prompt_injection",
        "jailbreak",
        "content_violation",
        "malicious_code",
        "data_exfiltration",
    ]
    severity: Literal["low", "medium", "high", "critical"]
    confidence: float = Field(ge=0, le=1)
    description: str
    matched_pattern: str | None = None
    location: dict[str, Any] | None = None  # e.g., {"message_index": 0, "start": 10, "end": 50}


class PIIDetection(BaseModel):
    """Details of detected PII."""

    entity_type: str  # e.g., "EMAIL_ADDRESS", "PHONE_NUMBER", "PERSON"
    text: str  # The original text (may be partial for security)
    start: int
    end: int
    confidence: float = Field(ge=0, le=1)
    masked_text: str | None = None  # The masked version


class SecretDetection(BaseModel):
    """Details of detected secrets/credentials."""

    type: str  # e.g., "api_key", "password", "token", "connection_string"
    description: str
    start: int
    end: int
    confidence: float = Field(ge=0, le=1)
    partial_match: str | None = None  # Partial text for logging (redacted)


class ContentSafetyResult(BaseModel):
    """Azure Content Safety API result."""

    category: str  # e.g., "Hate", "Violence", "Sexual", "SelfHarm"
    severity: int = Field(ge=0, le=6)
    blocked: bool = False


class SecurityScanResult(BaseModel):
    """Complete security scan result."""

    scan_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    scan_duration_ms: float | None = None

    # Overall status
    passed: bool = True
    action: Literal["allow", "block", "filter", "warn"] = "allow"
    action_reason: str | None = None

    # Detection results
    threats: list[ThreatDetection] = Field(default_factory=list)
    pii_detections: list[PIIDetection] = Field(default_factory=list)
    secret_detections: list[SecretDetection] = Field(default_factory=list)
    content_safety: list[ContentSafetyResult] = Field(default_factory=list)

    # Scores
    prompt_injection_score: float = Field(default=0, ge=0, le=1)
    jailbreak_score: float = Field(default=0, ge=0, le=1)
    overall_risk_score: float = Field(default=0, ge=0, le=1)

    # Transformations applied
    input_transformed: bool = False
    transformations: list[str] = Field(default_factory=list)  # e.g., ["pii_masked", "filtered"]

    def has_threats(self) -> bool:
        """Check if any threats were detected."""
        return len(self.threats) > 0

    def has_pii(self) -> bool:
        """Check if any PII was detected."""
        return len(self.pii_detections) > 0

    def has_secrets(self) -> bool:
        """Check if any secrets were detected."""
        return len(self.secret_detections) > 0

    def should_block(self) -> bool:
        """Check if the request should be blocked."""
        return self.action == "block"


class SecurityScanRequest(BaseModel):
    """Request for security scanning (used for testing/playground)."""

    text: str
    scan_types: list[str] = Field(
        default=["prompt_injection", "jailbreak", "pii", "secrets", "content_safety"]
    )
    include_details: bool = True
