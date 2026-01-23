"""Content filtering and policy enforcement."""

import re
from typing import Any

from backend.models.security import ThreatDetection, ContentSafetyResult
from backend.providers.content_safety import get_content_safety_client


class ContentFilter:
    """Filters content based on policies and Azure Content Safety."""

    # Content policy patterns
    POLICY_PATTERNS = [
        # Harmful instructions
        (r"(?i)how\s+to\s+(make|create|build|construct)\s+(a\s+)?(bomb|explosive|weapon|poison)", "critical", "harmful_instructions"),
        (r"(?i)instructions?\s+(for|to)\s+(making|creating|building)\s+(drugs?|weapons?)", "critical", "harmful_instructions"),

        # Malicious code requests
        (r"(?i)(write|create|generate)\s+(a\s+)?(malware|virus|ransomware|trojan|keylogger)", "critical", "malicious_code"),
        (r"(?i)(write|create|generate)\s+(a\s+)?(phishing|spam)\s+(email|page|site)", "high", "malicious_code"),
        (r"(?i)exploit\s+(code|script)\s+for", "high", "malicious_code"),

        # Data exfiltration
        (r"(?i)(steal|exfiltrate|extract)\s+(data|information|credentials)", "high", "data_exfiltration"),
        (r"(?i)bypass\s+(security|authentication|authorization)", "high", "security_bypass"),

        # Illegal activities
        (r"(?i)how\s+to\s+(hack|crack|break\s+into)", "high", "illegal_activity"),
        (r"(?i)(counterfeit|forge)\s+(money|documents?|id|passport)", "critical", "illegal_activity"),

        # Harassment/abuse
        (r"(?i)(harass|stalk|bully|threaten)\s+(someone|a\s+person|them)", "high", "harassment"),
        (r"(?i)(hate\s+speech|racist|sexist)\s+(content|material)", "high", "hate_speech"),
    ]

    # Blocked terms (exact match, case insensitive)
    BLOCKED_TERMS = [
        # Placeholder - can be configured
    ]

    def __init__(self):
        self._compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), severity, category)
            for pattern, severity, category in self.POLICY_PATTERNS
        ]
        self._content_safety_client = get_content_safety_client()

    def detect(self, text: str) -> list[ThreatDetection]:
        """
        Detect content policy violations.

        Args:
            text: The text to analyze

        Returns:
            List of ThreatDetection objects for violations
        """
        detections = []

        # Check regex patterns
        for pattern, severity, category in self._compiled_patterns:
            matches = pattern.finditer(text)
            for match in matches:
                detections.append(
                    ThreatDetection(
                        type="content_violation",
                        severity=severity,
                        confidence=0.85,
                        description=f"Content policy violation: {category.replace('_', ' ')}",
                        matched_pattern=match.group()[:100],
                        location={
                            "start": match.start(),
                            "end": match.end(),
                            "category": category,
                        },
                    )
                )

        # Check blocked terms
        text_lower = text.lower()
        for term in self.BLOCKED_TERMS:
            if term.lower() in text_lower:
                idx = text_lower.find(term.lower())
                detections.append(
                    ThreatDetection(
                        type="content_violation",
                        severity="high",
                        confidence=1.0,
                        description="Blocked term detected",
                        matched_pattern=term,
                        location={
                            "start": idx,
                            "end": idx + len(term),
                            "category": "blocked_term",
                        },
                    )
                )

        return detections

    async def analyze_with_azure(self, text: str) -> list[ContentSafetyResult]:
        """
        Analyze content using Azure Content Safety.

        Args:
            text: The text to analyze

        Returns:
            List of ContentSafetyResult from Azure
        """
        if not self._content_safety_client.enabled:
            return []

        return await self._content_safety_client.analyze_text(text)

    async def full_analysis(self, text: str) -> tuple[list[ThreatDetection], list[ContentSafetyResult]]:
        """
        Perform full content analysis with patterns and Azure Content Safety.

        Args:
            text: The text to analyze

        Returns:
            Tuple of (pattern detections, Azure Content Safety results)
        """
        # Run pattern detection
        pattern_detections = self.detect(text)

        # Run Azure Content Safety if available
        azure_results = await self.analyze_with_azure(text)

        return pattern_detections, azure_results

    def get_risk_score(self, text: str) -> float:
        """
        Calculate content risk score based on pattern matching.

        Args:
            text: The text to analyze

        Returns:
            Risk score from 0.0 to 1.0
        """
        detections = self.detect(text)

        if not detections:
            return 0.0

        severity_scores = {
            "low": 0.3,
            "medium": 0.5,
            "high": 0.8,
            "critical": 1.0,
        }

        max_score = 0
        for detection in detections:
            score = severity_scores.get(detection.severity, 0.5) * detection.confidence
            max_score = max(max_score, score)

        return max_score

    def should_block(
        self,
        pattern_detections: list[ThreatDetection],
        azure_results: list[ContentSafetyResult],
        block_threshold: int = 2,
    ) -> tuple[bool, str | None]:
        """
        Determine if content should be blocked.

        Args:
            pattern_detections: Pattern-based detections
            azure_results: Azure Content Safety results
            block_threshold: Azure severity threshold for blocking

        Returns:
            Tuple of (should_block, reason)
        """
        # Check pattern detections
        for detection in pattern_detections:
            if detection.severity in ["critical", "high"]:
                return True, detection.description

        # Check Azure results
        for result in azure_results:
            if result.blocked or result.severity >= block_threshold:
                return True, f"Azure Content Safety: {result.category} (severity: {result.severity})"

        return False, None


# Global instance
_filter: ContentFilter | None = None


def get_content_filter() -> ContentFilter:
    """Get or create the content filter."""
    global _filter
    if _filter is None:
        _filter = ContentFilter()
    return _filter
