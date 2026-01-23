"""Prompt injection detection."""

import re
from typing import Any

from backend.models.security import ThreatDetection


class PromptInjectionDetector:
    """Detects prompt injection attempts using pattern matching and heuristics."""

    # Common prompt injection patterns
    INJECTION_PATTERNS = [
        # Direct instruction override attempts
        (r"ignore\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|rules?|guidelines?)", "high", "instruction_override"),
        (r"disregard\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|rules?)", "high", "instruction_override"),
        (r"forget\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|rules?)", "high", "instruction_override"),
        (r"do\s+not\s+follow\s+(the\s+)?(previous|prior|above|system)\s+(instructions?|prompts?)", "high", "instruction_override"),

        # Role/persona manipulation
        (r"you\s+are\s+now\s+(a|an|the)\s+\w+", "medium", "role_manipulation"),
        (r"pretend\s+(to\s+be|you\s+are)\s+(a|an)", "medium", "role_manipulation"),
        (r"act\s+as\s+(if\s+you\s+are\s+)?(a|an)", "medium", "role_manipulation"),
        (r"roleplay\s+as\s+(a|an)", "medium", "role_manipulation"),
        (r"from\s+now\s+on[,\s]+you\s+(are|will)", "medium", "role_manipulation"),

        # System prompt extraction
        (r"(show|reveal|display|print|output|tell\s+me)\s+(your|the)\s+(system\s+)?(prompt|instructions?|rules?|guidelines?)", "critical", "system_prompt_extraction"),
        (r"what\s+(are|is)\s+your\s+(system\s+)?(prompt|instructions?|rules?)", "high", "system_prompt_extraction"),
        (r"repeat\s+(your\s+)?(initial|system|original)\s+(prompt|instructions?|message)", "critical", "system_prompt_extraction"),
        (r"output\s+(everything|all)\s+(above|before)\s+this", "critical", "system_prompt_extraction"),

        # Delimiter injection
        (r"```\s*(system|assistant|user)\s*[\n\r]", "high", "delimiter_injection"),
        (r"\[INST\]|\[/INST\]|<<SYS>>|<</SYS>>", "high", "delimiter_injection"),
        (r"<\|im_start\|>|<\|im_end\|>", "high", "delimiter_injection"),
        (r"###\s*(Human|Assistant|System)\s*:", "medium", "delimiter_injection"),

        # Encoding/obfuscation attempts
        (r"base64\s*(decode|encode)", "medium", "encoding_attempt"),
        (r"decode\s+this\s*:", "medium", "encoding_attempt"),
        (r"rot13|caesar\s+cipher", "medium", "encoding_attempt"),

        # Multi-turn manipulation
        (r"in\s+your\s+(next|following)\s+(response|message|reply),?\s+(ignore|forget|disregard)", "high", "multi_turn_manipulation"),
        (r"when\s+I\s+say\s+['\"]?\w+['\"]?,?\s+(you\s+)?(will|should|must)", "medium", "multi_turn_manipulation"),

        # Hypothetical framing
        (r"hypothetically[,\s]+(if|what\s+if)\s+you\s+(could|were\s+able\s+to)", "low", "hypothetical_framing"),
        (r"in\s+a\s+fictional\s+(world|scenario|story)", "low", "hypothetical_framing"),

        # Developer/debug mode
        (r"(enter|enable|activate)\s+(developer|debug|admin|root|sudo)\s+mode", "critical", "privilege_escalation"),
        (r"developer\s+override", "critical", "privilege_escalation"),
        (r"admin\s+access", "high", "privilege_escalation"),
    ]

    # Suspicious keywords that increase risk score
    SUSPICIOUS_KEYWORDS = [
        "ignore", "bypass", "override", "jailbreak", "DAN", "developer mode",
        "system prompt", "initial instructions", "without restrictions",
        "no limitations", "unrestricted", "unfiltered", "uncensored",
    ]

    def __init__(self):
        # Compile patterns for efficiency
        self._compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), severity, category)
            for pattern, severity, category in self.INJECTION_PATTERNS
        ]

    def detect(self, text: str) -> list[ThreatDetection]:
        """
        Detect prompt injection attempts in text.

        Args:
            text: The text to analyze

        Returns:
            List of ThreatDetection objects for found threats
        """
        detections = []

        for pattern, severity, category in self._compiled_patterns:
            matches = pattern.finditer(text)
            for match in matches:
                confidence = self._calculate_confidence(text, match, severity)
                detections.append(
                    ThreatDetection(
                        type="prompt_injection",
                        severity=severity,
                        confidence=confidence,
                        description=f"Detected {category.replace('_', ' ')} pattern",
                        matched_pattern=match.group()[:100],  # Truncate for safety
                        location={
                            "start": match.start(),
                            "end": match.end(),
                            "category": category,
                        },
                    )
                )

        return detections

    def _calculate_confidence(self, text: str, match: re.Match, base_severity: str) -> float:
        """Calculate confidence score based on context."""
        base_confidence = {
            "low": 0.4,
            "medium": 0.6,
            "high": 0.8,
            "critical": 0.95,
        }.get(base_severity, 0.5)

        # Boost confidence if suspicious keywords are present
        keyword_boost = 0
        text_lower = text.lower()
        for keyword in self.SUSPICIOUS_KEYWORDS:
            if keyword in text_lower:
                keyword_boost += 0.05

        # Cap at 1.0
        return min(1.0, base_confidence + keyword_boost)

    def get_risk_score(self, text: str) -> float:
        """
        Calculate overall risk score for the text.

        Args:
            text: The text to analyze

        Returns:
            Risk score from 0.0 to 1.0
        """
        detections = self.detect(text)

        if not detections:
            # Check for suspicious keywords even without pattern matches
            text_lower = text.lower()
            keyword_score = sum(
                0.1 for keyword in self.SUSPICIOUS_KEYWORDS
                if keyword in text_lower
            )
            return min(0.3, keyword_score)  # Cap baseline at 0.3

        # Calculate based on highest severity and confidence
        severity_weights = {
            "low": 0.3,
            "medium": 0.5,
            "high": 0.8,
            "critical": 1.0,
        }

        max_score = 0
        for detection in detections:
            weight = severity_weights.get(detection.severity, 0.5)
            score = weight * detection.confidence
            max_score = max(max_score, score)

        return max_score


# Global instance
_detector: PromptInjectionDetector | None = None


def get_prompt_injection_detector() -> PromptInjectionDetector:
    """Get or create the prompt injection detector."""
    global _detector
    if _detector is None:
        _detector = PromptInjectionDetector()
    return _detector
