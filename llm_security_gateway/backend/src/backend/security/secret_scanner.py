"""Secret and credential detection."""

import re
from typing import Any

from backend.models.security import SecretDetection


class SecretScanner:
    """Scans text for secrets, credentials, and sensitive tokens."""

    # Secret patterns with type and description
    SECRET_PATTERNS = [
        # API Keys - Generic
        (r"(?i)(api[_-]?key|apikey)['\"]?\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{20,})['\"]?", "api_key", "Generic API key"),

        # AWS
        (r"(?i)AKIA[0-9A-Z]{16}", "aws_access_key", "AWS Access Key ID"),
        (r"(?i)aws[_-]?secret[_-]?access[_-]?key['\"]?\s*[:=]\s*['\"]?([a-zA-Z0-9/+=]{40})['\"]?", "aws_secret_key", "AWS Secret Access Key"),

        # Azure
        (r"(?i)azure[_-]?(?:storage[_-]?)?(?:account[_-]?)?key['\"]?\s*[:=]\s*['\"]?([a-zA-Z0-9+/=]{88})['\"]?", "azure_storage_key", "Azure Storage Key"),
        (r"(?i)DefaultEndpointsProtocol=https;AccountName=[^;]+;AccountKey=[^;]+", "azure_connection_string", "Azure Connection String"),

        # Google Cloud
        (r"(?i)AIza[0-9A-Za-z_-]{35}", "gcp_api_key", "Google Cloud API Key"),
        (r'"type":\s*"service_account"', "gcp_service_account", "GCP Service Account JSON"),

        # GitHub
        (r"(?i)gh[pousr]_[A-Za-z0-9_]{36,}", "github_token", "GitHub Token"),
        (r"(?i)github[_-]?token['\"]?\s*[:=]\s*['\"]?([a-zA-Z0-9_]{40})['\"]?", "github_token", "GitHub Personal Access Token"),

        # Private Keys
        (r"-----BEGIN (?:RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----", "private_key", "Private Key"),
        (r"-----BEGIN PGP PRIVATE KEY BLOCK-----", "pgp_private_key", "PGP Private Key"),

        # Database Connection Strings
        (r"(?i)mongodb(?:\+srv)?://[^\s'\"]+", "mongodb_uri", "MongoDB Connection URI"),
        (r"(?i)postgres(?:ql)?://[^\s'\"]+", "postgres_uri", "PostgreSQL Connection URI"),
        (r"(?i)mysql://[^\s'\"]+", "mysql_uri", "MySQL Connection URI"),
        (r"(?i)redis://[^\s'\"]+", "redis_uri", "Redis Connection URI"),

        # JWT Tokens
        (r"eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*", "jwt_token", "JWT Token"),

        # Generic Passwords
        (r"(?i)password['\"]?\s*[:=]\s*['\"]?([^\s'\"]{8,})['\"]?", "password", "Password in plaintext"),
        (r"(?i)passwd['\"]?\s*[:=]\s*['\"]?([^\s'\"]{8,})['\"]?", "password", "Password in plaintext"),
        (r"(?i)secret['\"]?\s*[:=]\s*['\"]?([^\s'\"]{8,})['\"]?", "secret", "Secret value"),

        # Bearer Tokens
        (r"(?i)bearer\s+[a-zA-Z0-9_\-.]+", "bearer_token", "Bearer Token"),
        (r"(?i)authorization['\"]?\s*[:=]\s*['\"]?bearer\s+([^\s'\"]+)['\"]?", "bearer_token", "Authorization Bearer Token"),

        # Slack
        (r"xox[baprs]-[0-9]{10,13}-[0-9]{10,13}[a-zA-Z0-9-]*", "slack_token", "Slack Token"),

        # Stripe
        (r"(?i)sk_live_[0-9a-zA-Z]{24}", "stripe_secret_key", "Stripe Secret Key"),
        (r"(?i)sk_test_[0-9a-zA-Z]{24}", "stripe_test_key", "Stripe Test Key"),

        # Twilio
        (r"(?i)twilio[_-]?(?:auth[_-]?)?token['\"]?\s*[:=]\s*['\"]?([a-f0-9]{32})['\"]?", "twilio_token", "Twilio Auth Token"),

        # SendGrid
        (r"(?i)SG\.[a-zA-Z0-9_-]{22}\.[a-zA-Z0-9_-]{43}", "sendgrid_api_key", "SendGrid API Key"),

        # OpenAI
        (r"sk-[a-zA-Z0-9]{48}", "openai_api_key", "OpenAI API Key"),
        (r"sk-proj-[a-zA-Z0-9_-]{48,}", "openai_project_key", "OpenAI Project API Key"),

        # Anthropic
        (r"sk-ant-[a-zA-Z0-9_-]{40,}", "anthropic_api_key", "Anthropic API Key"),
    ]

    def __init__(self):
        self._compiled_patterns = [
            (re.compile(pattern), secret_type, description)
            for pattern, secret_type, description in self.SECRET_PATTERNS
        ]

    def detect(self, text: str) -> list[SecretDetection]:
        """
        Detect secrets and credentials in text.

        Args:
            text: The text to scan

        Returns:
            List of SecretDetection objects for found secrets
        """
        detections = []

        for pattern, secret_type, description in self._compiled_patterns:
            matches = pattern.finditer(text)
            for match in matches:
                # Get the matched text
                matched_text = match.group()

                # Create a redacted version for logging
                redacted = self._redact_secret(matched_text, secret_type)

                detections.append(
                    SecretDetection(
                        type=secret_type,
                        description=description,
                        start=match.start(),
                        end=match.end(),
                        confidence=0.9,  # High confidence for regex matches
                        partial_match=redacted,
                    )
                )

        return self._deduplicate_detections(detections)

    def _redact_secret(self, text: str, secret_type: str) -> str:
        """Create a redacted version of the secret for logging."""
        if len(text) <= 8:
            return "*" * len(text)

        # Show prefix for identification, redact the rest
        if secret_type in ["aws_access_key"]:
            return text[:4] + "*" * (len(text) - 4)
        elif secret_type in ["jwt_token"]:
            return text[:10] + "..." + "*" * 10
        elif secret_type in ["private_key", "pgp_private_key"]:
            return text[:30] + "...[REDACTED]"
        else:
            return text[:4] + "*" * min(len(text) - 8, 20) + text[-4:]

    def _deduplicate_detections(self, detections: list[SecretDetection]) -> list[SecretDetection]:
        """Remove duplicate detections at the same location."""
        if not detections:
            return []

        seen = set()
        unique = []

        for detection in detections:
            key = (detection.start, detection.end)
            if key not in seen:
                seen.add(key)
                unique.append(detection)

        return unique

    def mask(self, text: str) -> tuple[str, list[SecretDetection]]:
        """
        Detect and mask secrets in text.

        Args:
            text: The text to process

        Returns:
            Tuple of (masked_text, list of detections)
        """
        detections = self.detect(text)

        if not detections:
            return text, []

        # Sort by start position in reverse order for replacement
        sorted_detections = sorted(detections, key=lambda d: d.start, reverse=True)

        masked_text = text
        for detection in sorted_detections:
            placeholder = f"<{detection.type.upper()}>"
            masked_text = (
                masked_text[:detection.start]
                + placeholder
                + masked_text[detection.end:]
            )

        return masked_text, detections

    def get_risk_score(self, text: str) -> float:
        """
        Calculate secret exposure risk score.

        Args:
            text: The text to analyze

        Returns:
            Risk score from 0.0 to 1.0
        """
        detections = self.detect(text)

        if not detections:
            return 0.0

        # Weight different secret types
        weights = {
            "private_key": 1.0,
            "pgp_private_key": 1.0,
            "aws_secret_key": 1.0,
            "aws_access_key": 0.9,
            "azure_storage_key": 0.9,
            "azure_connection_string": 0.9,
            "gcp_service_account": 0.9,
            "password": 0.8,
            "jwt_token": 0.7,
            "openai_api_key": 0.7,
            "anthropic_api_key": 0.7,
            "api_key": 0.6,
            "bearer_token": 0.6,
        }

        max_score = 0
        for detection in detections:
            weight = weights.get(detection.type, 0.7)
            score = weight * detection.confidence
            max_score = max(max_score, score)

        return max_score


# Global instance
_scanner: SecretScanner | None = None


def get_secret_scanner() -> SecretScanner:
    """Get or create the secret scanner."""
    global _scanner
    if _scanner is None:
        _scanner = SecretScanner()
    return _scanner
