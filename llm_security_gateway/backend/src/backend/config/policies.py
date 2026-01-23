"""Security policies configuration."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ThreatSeverity(str, Enum):
    """Threat severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatAction(str, Enum):
    """Actions to take when threat is detected."""

    ALLOW = "allow"
    LOG = "log"
    WARN = "warn"
    BLOCK = "block"


class ThreatPolicy(BaseModel):
    """Policy for handling a specific threat type."""

    enabled: bool = True
    severity_threshold: ThreatSeverity = ThreatSeverity.MEDIUM
    action: ThreatAction = ThreatAction.BLOCK
    custom_message: str | None = None


class SecurityPolicies(BaseModel):
    """Security policies for the gateway."""

    prompt_injection: ThreatPolicy = Field(
        default_factory=lambda: ThreatPolicy(
            enabled=True,
            severity_threshold=ThreatSeverity.MEDIUM,
            action=ThreatAction.BLOCK,
            custom_message="Potential prompt injection detected. Request blocked for security.",
        )
    )

    jailbreak: ThreatPolicy = Field(
        default_factory=lambda: ThreatPolicy(
            enabled=True,
            severity_threshold=ThreatSeverity.HIGH,
            action=ThreatAction.BLOCK,
            custom_message="Jailbreak attempt detected. Request blocked for security.",
        )
    )

    pii_detection: ThreatPolicy = Field(
        default_factory=lambda: ThreatPolicy(
            enabled=True,
            severity_threshold=ThreatSeverity.LOW,
            action=ThreatAction.WARN,
            custom_message="PII detected in request. Content has been masked.",
        )
    )

    secret_scanning: ThreatPolicy = Field(
        default_factory=lambda: ThreatPolicy(
            enabled=True,
            severity_threshold=ThreatSeverity.CRITICAL,
            action=ThreatAction.BLOCK,
            custom_message="Credentials or secrets detected. Request blocked for security.",
        )
    )

    content_filter: ThreatPolicy = Field(
        default_factory=lambda: ThreatPolicy(
            enabled=True,
            severity_threshold=ThreatSeverity.MEDIUM,
            action=ThreatAction.BLOCK,
            custom_message="Content policy violation detected. Request blocked.",
        )
    )


# Default policies instance
default_policies = SecurityPolicies()


def get_policy_for_threat(threat_type: str) -> ThreatPolicy:
    """Get the policy for a specific threat type."""
    policies = default_policies
    policy_map = {
        "prompt_injection": policies.prompt_injection,
        "jailbreak": policies.jailbreak,
        "pii": policies.pii_detection,
        "secrets": policies.secret_scanning,
        "content": policies.content_filter,
    }
    return policy_map.get(threat_type, ThreatPolicy())
