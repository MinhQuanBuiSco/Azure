"""Unified security scanner combining all detection methods."""

import time
import uuid
from typing import Any

from backend.config.settings import get_settings
from backend.config.policies import ThreatAction, get_policy_for_threat
from backend.models.security import (
    SecurityScanResult,
    ThreatDetection,
    PIIDetection,
    SecretDetection,
)
from backend.security.prompt_injection import get_prompt_injection_detector
from backend.security.jailbreak_detector import get_jailbreak_detector
from backend.security.pii_detector import get_pii_detector
from backend.security.secret_scanner import get_secret_scanner
from backend.security.content_filter import get_content_filter


class SecurityScanner:
    """Unified security scanner that orchestrates all security checks."""

    def __init__(self):
        self.settings = get_settings()
        self._prompt_injection_detector = get_prompt_injection_detector()
        self._jailbreak_detector = get_jailbreak_detector()
        self._pii_detector = get_pii_detector()
        self._secret_scanner = get_secret_scanner()
        self._content_filter = get_content_filter()

    async def scan(
        self,
        text: str,
        scan_types: list[str] | None = None,
        mask_pii: bool = True,
        mask_secrets: bool = True,
    ) -> tuple[SecurityScanResult, str]:
        """
        Perform comprehensive security scan on text.

        Args:
            text: The text to scan
            scan_types: List of scan types to perform (default: all)
            mask_pii: Whether to mask detected PII
            mask_secrets: Whether to mask detected secrets

        Returns:
            Tuple of (SecurityScanResult, processed_text)
        """
        start_time = time.time()
        scan_id = str(uuid.uuid4())

        # Default to all scan types
        if scan_types is None:
            scan_types = ["prompt_injection", "jailbreak", "pii", "secrets", "content_safety"]

        # Initialize results
        threats: list[ThreatDetection] = []
        pii_detections: list[PIIDetection] = []
        secret_detections: list[SecretDetection] = []
        content_safety_results = []
        transformations = []
        processed_text = text

        # Track scores
        prompt_injection_score = 0.0
        jailbreak_score = 0.0

        # Prompt injection detection
        if "prompt_injection" in scan_types and self.settings.enable_prompt_injection_detection:
            injection_threats = self._prompt_injection_detector.detect(text)
            threats.extend(injection_threats)
            prompt_injection_score = self._prompt_injection_detector.get_risk_score(text)

        # Jailbreak detection
        if "jailbreak" in scan_types and self.settings.enable_jailbreak_detection:
            jailbreak_threats = self._jailbreak_detector.detect(text)
            threats.extend(jailbreak_threats)
            jailbreak_score = self._jailbreak_detector.get_risk_score(text)

        # PII detection
        if "pii" in scan_types and self.settings.enable_pii_detection:
            if mask_pii and self.settings.pii_action == "mask":
                processed_text, pii_detections = self._pii_detector.mask(processed_text)
                if pii_detections:
                    transformations.append("pii_masked")
            else:
                pii_detections = self._pii_detector.detect(text)

        # Secret scanning
        if "secrets" in scan_types and self.settings.enable_secret_scanning:
            if mask_secrets:
                processed_text, secret_detections = self._secret_scanner.mask(processed_text)
                if secret_detections:
                    transformations.append("secrets_masked")
            else:
                secret_detections = self._secret_scanner.detect(text)

        # Content filtering
        if "content_safety" in scan_types and self.settings.enable_content_filtering:
            content_threats, content_safety_results = await self._content_filter.full_analysis(text)
            threats.extend(content_threats)

        # Calculate overall risk score
        overall_risk_score = max(
            prompt_injection_score,
            jailbreak_score,
            self._pii_detector.get_risk_score(text) if pii_detections else 0,
            self._secret_scanner.get_risk_score(text) if secret_detections else 0,
            self._content_filter.get_risk_score(text),
        )

        # Determine action
        action, action_reason = self._determine_action(
            threats, pii_detections, secret_detections, content_safety_results
        )

        scan_duration = (time.time() - start_time) * 1000  # Convert to ms

        result = SecurityScanResult(
            scan_id=scan_id,
            scan_duration_ms=scan_duration,
            passed=action != "block",
            action=action,
            action_reason=action_reason,
            threats=threats,
            pii_detections=pii_detections,
            secret_detections=secret_detections,
            content_safety=content_safety_results,
            prompt_injection_score=prompt_injection_score,
            jailbreak_score=jailbreak_score,
            overall_risk_score=overall_risk_score,
            input_transformed=bool(transformations),
            transformations=transformations,
        )

        return result, processed_text

    def _determine_action(
        self,
        threats: list[ThreatDetection],
        pii_detections: list[PIIDetection],
        secret_detections: list[SecretDetection],
        content_safety_results: list,
    ) -> tuple[str, str | None]:
        """
        Determine the action to take based on scan results.

        Returns:
            Tuple of (action, reason)
        """
        # Check threats (prompt injection, jailbreak, content violations)
        for threat in threats:
            if threat.severity in ["critical", "high"]:
                policy = get_policy_for_threat(threat.type)
                if policy.action == ThreatAction.BLOCK:
                    return "block", policy.custom_message or threat.description

        # Check for blocking based on secrets
        if secret_detections:
            policy = get_policy_for_threat("secrets")
            if policy.action == ThreatAction.BLOCK:
                return "block", policy.custom_message or "Credentials or secrets detected"

        # Check content safety results
        for cs_result in content_safety_results:
            if cs_result.blocked:
                return "block", f"Content Safety: {cs_result.category}"

        # Check if any transformations were applied (filtering/masking)
        if pii_detections or secret_detections:
            return "filter", "Content was filtered/masked"

        # Check for warnings
        for threat in threats:
            if threat.severity in ["medium", "low"]:
                policy = get_policy_for_threat(threat.type)
                if policy.action == ThreatAction.WARN:
                    return "warn", threat.description

        return "allow", None

    async def scan_messages(
        self,
        messages: list[dict[str, Any]],
        scan_types: list[str] | None = None,
    ) -> tuple[SecurityScanResult, list[dict[str, Any]]]:
        """
        Scan a list of chat messages.

        Args:
            messages: List of message dicts with 'role' and 'content'
            scan_types: List of scan types to perform

        Returns:
            Tuple of (combined SecurityScanResult, processed messages)
        """
        all_threats = []
        all_pii = []
        all_secrets = []
        all_content_safety = []
        all_transformations = []

        processed_messages = []
        max_risk = 0.0
        max_injection_score = 0.0
        max_jailbreak_score = 0.0
        total_duration = 0.0

        for msg in messages:
            content = msg.get("content", "")
            if not content or not isinstance(content, str):
                processed_messages.append(msg)
                continue

            # Scan the message content
            result, processed_content = await self.scan(content, scan_types)

            # Aggregate results
            all_threats.extend(result.threats)
            all_pii.extend(result.pii_detections)
            all_secrets.extend(result.secret_detections)
            all_content_safety.extend(result.content_safety)
            all_transformations.extend(result.transformations)

            max_risk = max(max_risk, result.overall_risk_score)
            max_injection_score = max(max_injection_score, result.prompt_injection_score)
            max_jailbreak_score = max(max_jailbreak_score, result.jailbreak_score)
            total_duration += result.scan_duration_ms or 0

            # Create processed message
            processed_msg = msg.copy()
            processed_msg["content"] = processed_content
            processed_messages.append(processed_msg)

            # Early exit if blocked
            if result.should_block():
                break

        # Determine overall action
        action, action_reason = self._determine_action(
            all_threats, all_pii, all_secrets, all_content_safety
        )

        combined_result = SecurityScanResult(
            scan_id=str(uuid.uuid4()),
            scan_duration_ms=total_duration,
            passed=action != "block",
            action=action,
            action_reason=action_reason,
            threats=all_threats,
            pii_detections=all_pii,
            secret_detections=all_secrets,
            content_safety=all_content_safety,
            prompt_injection_score=max_injection_score,
            jailbreak_score=max_jailbreak_score,
            overall_risk_score=max_risk,
            input_transformed=bool(all_transformations),
            transformations=list(set(all_transformations)),
        )

        return combined_result, processed_messages


# Global instance
_scanner: SecurityScanner | None = None


def get_security_scanner() -> SecurityScanner:
    """Get or create the security scanner."""
    global _scanner
    if _scanner is None:
        _scanner = SecurityScanner()
    return _scanner
